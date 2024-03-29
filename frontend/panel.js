'use strict'
import { twitch, extensionUri } from './globals.js'

let authorization


twitch.onAuthorized(function (auth) {
  authorization = 'Bearer ' + auth.token
  console.log('bits enabled: ' + twitch.features.isBitsEnabled)
})

twitch.listen("broadcast", function (target, contentType, message) {
  console.log(`target ${target} contentType ${contentType} message ${message}`)

  if (message === "refresh") {
    // refresh after a random interval between 0-5s (to reduce ebs load)
    setTimeout(function () {
      htmx.trigger("#layout-loader", "refresh")
    }, Math.floor(Math.random() * 5000))
  }
})

htmx.on("htmx:afterSwap", (e) => {
  console.log("swap")
  // Response targeting #dialog => show the modal
  if (e.detail.target.id == "layout") {
    var webhookButtons = document.querySelectorAll(".webhook-button");
    for (var i = 0; i < webhookButtons.length; i++) {
      var webhookButton = webhookButtons[i];
      const webhookID = webhookButton.getAttribute("data-id")
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

async function webhookRedeem (webhookID, webhookBitsProduct) {
  console.log(webhookID)
  console.log(webhookBitsProduct)
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
    console.log("test")
  } catch (error) {
    console.error(error)
  } finally {
    twitch.bits.onTransactionComplete(() => {});
    twitch.bits.onTransactionCancelled(() => {});
  }
}
