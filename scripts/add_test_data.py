"""Load the database with test data."""

import os
from mulletwebhook import create_app
from mulletwebhook.database import db

from mulletwebhook.models.broadcaster import Broadcaster
from mulletwebhook.models.layout import Layout
from mulletwebhook.models.element import Element, Image, Text, Webhook
from mulletwebhook.models.enums import ElementType, BitsProduct

from mulletwebhook import utils

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

with open(f"{SCRIPT_DIR}/../images/jaedolph.png", "rb") as image:
    jaedolph_image = image.read()

with open(f"{SCRIPT_DIR}/../images/mulletwebhook-logo-small.png", "rb") as image:
    mullet_image = image.read()


def main() -> None:
    """Initializes the database."""
    with create_app().app_context():

        broadcaster = Broadcaster(id=25819608, current_layout=1, editing_layout=1)
        db.session.add(broadcaster)

        layout = Layout(
            name="example layout",
            title="Jaedolph v Mullet",
            broadcaster_id=broadcaster.id,
        )
        db.session.add(layout)
        db.session.commit()

        element1 = Element(
            element_type=ElementType.image,
            layout_id=layout.id,
            position=utils.get_next_layout_position(layout.id),
        )
        db.session.add(element1)
        db.session.commit()

        image = Image(data=jaedolph_image, element_id=element1.id, filename="jaedolph.png")
        db.session.add(image)
        db.session.commit()

        element2 = Element(
            element_type=ElementType.image,
            layout_id=layout.id,
            position=utils.get_next_layout_position(layout.id),
        )
        db.session.add(element2)
        db.session.commit()

        image = Image(data=mullet_image, element_id=element2.id, filename="mullet.png")
        db.session.add(image)
        db.session.commit()

        element3 = Element(
            element_type=ElementType.text,
            layout_id=layout.id,
            position=utils.get_next_layout_position(layout.id),
        )
        db.session.add(element3)
        db.session.commit()

        text = Text(text="Troll Jaedolph:", element_id=element3.id)
        db.session.add(text)
        db.session.commit()

        element4 = Element(
            element_type=ElementType.text,
            layout_id=layout.id,
            position=utils.get_next_layout_position(layout.id),
        )
        db.session.add(element4)
        db.session.commit()

        text = Text(text="Troll Mullet:", element_id=element4.id)
        db.session.add(text)
        db.session.commit()

        element5 = Element(
            element_type=ElementType.webhook,
            layout_id=layout.id,
            position=utils.get_next_layout_position(layout.id),
        )
        db.session.add(element5)
        db.session.commit()

        webhook = Webhook(
            name="Tripcraft (Jaedolph)",
            url="https://webhook.site/4cf830d1-6fa6-40b1-a682-cd7bd8315747",
            data={"user": "jaedolph", "redeem": "tripcraft"},
            bits_product=BitsProduct.reward_1bits,
            element_id=element5.id,
        )

        db.session.add(webhook)
        db.session.commit()

        element6 = Element(
            element_type=ElementType.webhook,
            layout_id=layout.id,
            position=utils.get_next_layout_position(layout.id),
        )
        db.session.add(element6)
        db.session.commit()

        webhook = Webhook(
            name="Tripcraft (Mullet)",
            url="https://webhook.site/4cf830d1-6fa6-40b1-a682-cd7bd8315747",
            data={"user": "mullet", "redeem": "tripcraft"},
            bits_product=BitsProduct.reward_1bits,
            element_id=element6.id,
        )
        db.session.add(webhook)
        db.session.commit()

        element7 = Element(
            element_type=ElementType.webhook,
            layout_id=layout.id,
            position=utils.get_next_layout_position(layout.id),
        )
        db.session.add(element7)
        db.session.commit()

        webhook = Webhook(
            name="Invert Screen (Jaedolph)",
            url="https://webhook.site/4cf830d1-6fa6-40b1-a682-cd7bd8315747",
            data={"user": "jaedolph", "redeem": "invert_screen"},
            bits_product=BitsProduct.reward_1bits,
            element_id=element7.id,
        )

        db.session.add(webhook)
        db.session.commit()

        element8 = Element(
            element_type=ElementType.webhook,
            layout_id=layout.id,
            position=utils.get_next_layout_position(layout.id),
        )
        db.session.add(element8)
        db.session.commit()

        webhook = Webhook(
            name="Invert Screen (Mullet)",
            url="https://webhook.site/4cf830d1-6fa6-40b1-a682-cd7bd8315747",
            data={"user": "mullet", "redeem": "invert_screen"},
            bits_product=BitsProduct.reward_1bits,
            element_id=element8.id,
        )
        db.session.add(webhook)
        db.session.commit()

if __name__ == "__main__":
    main()
