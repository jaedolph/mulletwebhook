'use strict'
import { twitch, extensionUri } from './globals.js'

let authorization


twitch.onAuthorized(function (auth) {
  authorization = 'Bearer ' + auth.token
  // wait for user to be authorized before getting content for layout-loader
  htmx.trigger("#layout-loader", "authed")
})


htmx.on("htmx:configRequest", (e)=> {
  // add the auth token to the request as a header
  e.detail.headers["Authorization"] = authorization
  // update the URL to the proper extension URI
  if  (!e.detail.path.startsWith("https")) {
    e.detail.path = extensionUri + e.detail.path
  }
})

twitch.listen("broadcast", function (target, contentType, message) {
  // handle refreshing the panel if the streamer updates the layout
  if (message === "refresh") {
    // refresh after a random interval between 0-5s (to reduce EBS load)
    setTimeout(function () {
      htmx.trigger("#layout-loader", "refresh")
    }, Math.floor(Math.random() * 5000))
  }
})

htmx.on("htmx:afterSwap", (e) => {

  // start a bits transaction if the user clicks one of the webhook buttons
  if (e.detail.target.id == "layout") {
    var webhookButtons = document.querySelectorAll(".webhook-button");
    for (var i = 0; i < webhookButtons.length; i++) {
      var webhookButton = webhookButtons[i];
      // the webhookId is available in the data-id attribute of the button
      const webhookID = webhookButton.getAttribute("data-id")
      // the bitsProduct is available in the data-product attribute of the button
      const webhookBitsProduct = webhookButton.getAttribute("data-product")
      webhookButton.addEventListener(
        "click",
        async function () {
          webhookRedeem(webhookID, webhookBitsProduct)
        },
        false,
      )
    }
  }
})


// handle the bits transaction and trigger the webhook in the EBS if successful
async function webhookRedeem (webhookID, webhookBitsProduct) {
  try {
    const bitsTransaction = new Promise((complete, cancel) => {
      twitch.bits.onTransactionComplete(complete);
      twitch.bits.onTransactionCancelled(cancel);
    })
    twitch.bits.useBits(webhookBitsProduct);
    const tx = await bitsTransaction;

    const response = await fetch(
      extensionUri + '/webhook/' + webhookID, {
        method: "POST",
        headers: {
          'Content-Type': 'application/json',
          Authorization: authorization
        },
        body: JSON.stringify({"transaction": tx})
      }
    )
  } catch (error) {
    console.error(error)
  } finally {
    twitch.bits.onTransactionComplete(() => {});
    twitch.bits.onTransactionCancelled(() => {});
  }
}
