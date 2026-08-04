from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from database import Base2


class team_managment_db(Base2):
    __tablename__ = "team_db"

    # SQLAlchemy 2.x arbeitet bevorzugt mit Mapped-Annotations.
    # Dadurch kann der Editor die Spalten korrekt erkennen und die Typfehler verschwinden.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="neu")
    no_damage_to: Mapped[str] = mapped_column(String(255), default="")
    half_damage_to: Mapped[str] = mapped_column(String(255), default="")
    double_damage_to: Mapped[str] = mapped_column(String(255), default="")
    double_damage_from: Mapped[str] = mapped_column(String(255), default="")
    half_damage_from: Mapped[str] = mapped_column(String(255), default="")
    no_damage_from: Mapped[str] = mapped_column(String(255), default="")

    __table_args__ = (
        CheckConstraint("id BETWEEN 1 AND 6", name="check_team_id_range_1_to_6"),
    )
