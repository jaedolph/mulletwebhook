# mulletwebhook
Allows streamers to create custom webhook rewards that can be redeemed by users.

When a user purchases a reward the webhook will be triggered. This can be used to interact with services such as Mixitup.

## Create release zipfile

```
./scripts/install_js_deps.sh
./scripts/package_frontend.sh <version num>
```
The zipfile will be created in `dist/`

## Development

Run tox tests for EBS:
```
tox -c ebs/tox.ini
```
