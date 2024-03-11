"""Perform initial load of the database."""

from mulletwebhook import create_app
from mulletwebhook.database import db
from base64 import b64decode

from mulletwebhook.models.broadcaster import Broadcaster
from mulletwebhook.models.layout import Layout
from mulletwebhook.models.element import Element, Image, Text, Webhook, ElementType

with open("jaedolph.png", "rb") as image:
    jaedolph_image = image.read()

with open("mullet.png", "rb") as image:
    mullet_image = image.read()

def main() -> None:
    """Initializes the database."""
    with create_app().app_context():
        db.drop_all()
        db.create_all()
        broadcaster = Broadcaster(id=25819608,name="jaedolph")
        db.session.add(broadcaster)

        layout = Layout(name="my layout",title="Jaedolph v Mullet", broadcaster_id=broadcaster.id, columns=2)
        db.session.add(layout)
        db.session.commit()

        element1 = Element(element_type=ElementType.image, layout=layout.id, position=0)
        db.session.add(element1)
        db.session.commit()

        image = Image(data=jaedolph_image, element_id=element1.id)
        db.session.add(image)
        db.session.commit()

        element2 = Element(element_type=ElementType.image, layout=layout.id, position=1)
        db.session.add(element2)
        db.session.commit()

        image = Image(data=mullet_image, element_id=element2.id)
        db.session.add(image)
        db.session.commit()

        element3 = Element(element_type=ElementType.text, layout=layout.id, position=2)
        db.session.add(element3)
        db.session.commit()

        text = Text(text="Troll Jaedolph:", element_id=element3.id)
        db.session.add(text)
        db.session.commit()

        element4 = Element(element_type=ElementType.text, layout=layout.id, position=3)
        db.session.add(element4)
        db.session.commit()

        text = Text(text="Troll Mullet:", element_id=element4.id)
        db.session.add(text)
        db.session.commit()

        element5 = Element(element_type=ElementType.webhook, layout=layout.id, position=4)
        db.session.add(element5)
        db.session.commit()

        webhook = Webhook(
            text="Tripcraft",
            url="https://api.mixitupapp.com/api/webhook/69589292-d66b-4343-df35-08dc37d3f57c?secret=197B9B3FE10B3239E50D22F4C04D45142E9CC29C8579AE416695054056638D47",
            data='{"user": "jaedolph", "redeem": "tripcraft"}',
            bits_product="webhook_1bit",
            element_id=element5.id,
        )

        db.session.add(webhook)
        db.session.commit()

        element6 = Element(element_type=ElementType.webhook, layout=layout.id, position=5)
        db.session.add(element6)
        db.session.commit()

        webhook = Webhook(
            text="Tripcraft",
            url="https://api.mixitupapp.com/api/webhook/69589292-d66b-4343-df35-08dc37d3f57c?secret=197B9B3FE10B3239E50D22F4C04D45142E9CC29C8579AE416695054056638D47",
            data='{"user": "mullet", "redeem": "tripcraft"}',
            bits_product="webhook_1bit",
            element_id=element6.id,
        )
        db.session.add(webhook)
        db.session.commit()

        element7 = Element(element_type=ElementType.webhook, layout=layout.id, position=6)
        db.session.add(element7)
        db.session.commit()


        webhook = Webhook(
            text="Invert Screen",
            url="https://api.mixitupapp.com/api/webhook/69589292-d66b-4343-df35-08dc37d3f57c?secret=197B9B3FE10B3239E50D22F4C04D45142E9CC29C8579AE416695054056638D47",
            data='{"user": "jaedolph", "redeem": "invert_screen"}',
            bits_product="webhook_1bit",
            element_id=element7.id,
        )

        db.session.add(webhook)
        db.session.commit()

        element8 = Element(element_type=ElementType.webhook, layout=layout.id, position=7)
        db.session.add(element8)
        db.session.commit()

        webhook = Webhook(
            text="Invert Screen",
            url="https://api.mixitupapp.com/api/webhook/69589292-d66b-4343-df35-08dc37d3f57c?secret=197B9B3FE10B3239E50D22F4C04D45142E9CC29C8579AE416695054056638D47",
            data='{"user": "mullet", "redeem": "invert_screen"}',
            bits_product="webhook_1bit",
            element_id=element8.id,
        )
        db.session.add(webhook)
        db.session.commit()

        element9 = Element(element_type=ElementType.image, layout=layout.id, position=8)
        db.session.add(element9)
        db.session.commit()

        image = Image(data=jaedolph_image, element_id=element9.id)
        db.session.add(image)
        db.session.commit()

        element10 = Element(element_type=ElementType.image, layout=layout.id, position=9)
        db.session.add(element10)
        db.session.commit()

        image = Image(data=mullet_image, element_id=element10.id)
        db.session.add(image)
        db.session.commit()


if __name__ == "__main__":
    main()
