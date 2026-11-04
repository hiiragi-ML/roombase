from sqlalchemy.orm import Session

from .database import engine
from .models import Room

def seed_rooms():
    with Session(engine) as session:
        existing_room = session.get(Room, "main")
        if existing_room is None:
            room = Room(
                id="main",
                name="サークル部室",
                description="共用部室",
                capacity=20,
                color="#6658df",
                amenities=[],
            )

            session.add(room)
            session.commit()

            print("部室を登録しました")
        else:
            print("部室はすでに登録されています")

if __name__ == '__main__':
    seed_rooms()