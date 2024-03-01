"""Perform initial load of the database."""

from mulletwebhook import create_app
from mulletwebhook.database import db
from base64 import b64decode

from mulletwebhook.models.broadcaster import Broadcaster
from mulletwebhook.models.layout import Layout
from mulletwebhook.models.element import Element, Image, Text, Webhook, ElementType

with open("jaedolF.png", "rb") as image:
    test_image = image.read()

def main() -> None:
    """Initializes the database."""
    with create_app().app_context():
        db.drop_all()
        db.create_all()
        broadcaster = Broadcaster(id=25819608,name="jaedolph")
        db.session.add(broadcaster)

        layout = Layout(name="my layout", broadcaster_id=broadcaster.id, columns=2)
        db.session.add(layout)
        db.session.commit()

        element1 = Element(element_type=ElementType.image, layout=layout.id, position=0)
        db.session.add(element1)
        db.session.commit()

        image = Image(data=test_image, element_id=element1.id)
        db.session.add(image)
        db.session.commit()

        element2 = Element(element_type=ElementType.image, layout=layout.id, position=1)
        db.session.add(element2)
        db.session.commit()

        image = Image(data=test_image, element_id=element2.id)
        db.session.add(image)
        db.session.commit()

        element3 = Element(element_type=ElementType.text, layout=layout.id, position=2)
        db.session.add(element3)
        db.session.commit()

        text = Text(text="test text1", element_id=element3.id)
        db.session.add(text)
        db.session.commit()

        element4 = Element(element_type=ElementType.text, layout=layout.id, position=3)
        db.session.add(element4)
        db.session.commit()

        text = Text(text="test text2", element_id=element4.id)
        db.session.add(text)
        db.session.commit()

if __name__ == "__main__":
    main()
