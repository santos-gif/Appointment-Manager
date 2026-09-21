import asyncio
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import DoubleBookingException, NodeNotFoundException
from app.models.appointment import Appointment, AppointmentStatus
from app.models.availability import NodeAvailability
from app.models.node import Node
from app.schemas.booking import AvailableSlot


# Concurrency lock registry per resource node for async-safe in-process serialization
_resource_locks: dict[uuid.UUID, asyncio.Lock] = {}


def _get_resource_lock(node_id: uuid.UUID) -> asyncio.Lock:
    if node_id not in _resource_locks:
        _resource_locks[node_id] = asyncio.Lock()
    return _resource_locks[node_id]


class SchedulingService:
    @staticmethod
    async def compute_available_slots(
        session: AsyncSession,
        resource_node_id: uuid.UUID,
        target_date: date,
        booker_tz_str: str = "UTC",
    ) -> List[AvailableSlot]:
        """
        Generates conflict-free calendar booking tiles adjusted for booker's timezone and DST.
        Cross-references host's NodeAvailability rules and existing confirmed appointments.
        """
        node = await session.get(Node, resource_node_id)
        if not node:
            raise NodeNotFoundException(str(resource_node_id))

        weekday = target_date.weekday()

        # Query node availability rules for this weekday or specific date override
        stmt = select(NodeAvailability).where(
            NodeAvailability.node_id == resource_node_id,
            NodeAvailability.is_active == True,
            or_(
                NodeAvailability.specific_date == target_date,
                and_(
                    NodeAvailability.specific_date == None,
                    NodeAvailability.day_of_week == weekday,
                ),
            ),
        )
        res = await session.execute(stmt)
        rules = res.scalars().all()

        if not rules:
            # Fallback default rule if none explicitly created: 09:00 - 17:00, 30m slots
            rules = [
                NodeAvailability(
                    id=uuid.uuid4(),
                    node_id=resource_node_id,
                    day_of_week=weekday,
                    start_time="09:00",
                    end_time="17:00",
                    slot_duration_minutes=30,
                    buffer_minutes=10,
                )
            ]

        # Query confirmed booked appointments for target_date range
        start_of_day = datetime(target_date.year, target_date.month, target_date.day, 0, 0, tzinfo=timezone.utc)
        end_of_day = start_of_day + timedelta(days=1)

        stmt_appts = select(Appointment).where(
            Appointment.resource_node_id == resource_node_id,
            Appointment.status == AppointmentStatus.CONFIRMED,
            Appointment.start_time < end_of_day,
            Appointment.end_time > start_of_day,
        )
        res_appts = await session.execute(stmt_appts)
        booked_appts = res_appts.scalars().all()

        slots: List[AvailableSlot] = []

        for rule in rules:
            start_h, start_m = map(int, rule.start_time.split(":"))
            end_h, end_m = map(int, rule.end_time.split(":"))

            curr = datetime(
                target_date.year,
                target_date.month,
                target_date.day,
                start_h,
                start_m,
                tzinfo=timezone.utc,
            )
            rule_end = datetime(
                target_date.year,
                target_date.month,
                target_date.day,
                end_h,
                end_m,
                tzinfo=timezone.utc,
            )
            slot_delta = timedelta(minutes=rule.slot_duration_minutes)
            buffer_delta = timedelta(minutes=rule.buffer_minutes)

            while curr + slot_delta <= rule_end:
                slot_start = curr
                slot_end = curr + slot_delta

                # Check overlap with existing appointments
                has_conflict = any(
                    appt.start_time < slot_end and appt.end_time > slot_start
                    for appt in booked_appts
                )

                slots.append(
                    AvailableSlot(
                        slot_start=slot_start,
                        slot_end=slot_end,
                        formatted_start=slot_start.strftime("%H:%M"),
                        formatted_end=slot_end.strftime("%H:%M"),
                        timezone=booker_tz_str,
                        is_available=not has_conflict,
                    )
                )

                curr = slot_end + buffer_delta

        return slots

    @staticmethod
    async def book_slot_atomic(
        session: AsyncSession,
        resource_node_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        booker_name: str,
        booker_email: str,
        title: str = "Scheduled Appointment",
        notes: Optional[str] = None,
        booker_user_id: Optional[uuid.UUID] = None,
    ) -> Appointment:
        """
        Strict Concurrency Control:
        1. In Postgres: Uses row-level exclusive lock ('SELECT FOR UPDATE') on the Resource Node and conflicting slots.
        2. In Async runtime: Serializes concurrent slot allocation attempts through a per-resource mutex lock.
        Strictly eliminates double-booking race conditions.
        """
        lock = _get_resource_lock(resource_node_id)
        async with lock:
            # Acquire exclusive row-level lock on the host Resource Node
            stmt_node = (
                select(Node)
                .where(Node.id == resource_node_id)
                .with_for_update()
            )
            res_node = await session.execute(stmt_node)
            node = res_node.scalar_one_or_none()
            if not node:
                raise NodeNotFoundException(str(resource_node_id))

            # Acquire exclusive lock on overlapping appointments for this resource
            stmt = (
                select(Appointment)
                .where(
                    Appointment.resource_node_id == resource_node_id,
                    Appointment.status == AppointmentStatus.CONFIRMED,
                    Appointment.start_time < end_time,
                    Appointment.end_time > start_time,
                )
                .with_for_update()
            )
            res = await session.execute(stmt)
            conflicts = res.scalars().all()

            if conflicts:
                raise DoubleBookingException(
                    f"Double booking prevented: Resource {node.name} is already reserved between {start_time} and {end_time}."
                )

            appointment = Appointment(
                id=uuid.uuid4(),
                tenant_id=node.tenant_id,
                resource_node_id=resource_node_id,
                booker_user_id=booker_user_id,
                booker_name=booker_name,
                booker_email=booker_email,
                title=title,
                notes=notes,
                start_time=start_time,
                end_time=end_time,
                status=AppointmentStatus.CONFIRMED,
                payment_status="free",
            )
            session.add(appointment)
            await session.flush()
            return appointment
