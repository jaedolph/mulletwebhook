// The "Verified First Chatters" panel displayed to viewers

'use strict'
import { twitch, extensionUri } from './globals.js'

let authorization


twitch.onAuthorized(function (auth) {
  authorization = 'Bearer ' + auth.token
  console.log('bits enabled: ' + twitch.features.isBitsEnabled)

  //twitch.bits.setUseLoopback(true)
})

await renderLayout()

// const jaedolphButton = document.getElementById('jaedolph')
// jaedolphButton.addEventListener('click', jaedolphWebhook)

// const mulletButton = document.getElementById('mullet')
// mulletButton.addEventListener('click', mulletWebhook)


async function renderLayout () {
  console.debug("layout")
  const response = await fetch(
    extensionUri + '/layout/1', {
      method: "GET",
    }
  )

  const layout = await response.json()
  console.debug(layout)
  const elements = layout["elements"]
  const mainPanel = document.getElementById('mainPanel')
  let pannelInner = ""
  for (const index in elements){

    const element = elements[index]
    console.log(element)
    const element_type = element["type"]
    console.log(element_type)
    if (element_type == "image") {
      const element_id = element["id"]
      pannelInner += `<div><img src="${extensionUri}/image/${element_id}" class="center"></div>`
    }
    if (element_type == "text") {
      const text = element["text"]
      pannelInner += `<div><p class="center">${text}</p></div>`
    }

  }

  mainPanel.innerHTML = pannelInner


}

async function jaedolphWebhook () {
  await webhookRedeem("jaedolph")
}

async function mulletWebhook () {
  await webhookRedeem("mullet")
}

async function webhookRedeem (redeem) {
  try {
    let productSku = 'webhook_1bit';
    const bitsTransaction = new Promise((complete, cancel) => {
      twitch.bits.onTransactionComplete(complete);
      twitch.bits.onTransactionCancelled(cancel);
    })
    twitch.bits.useBits(productSku);
    const tx = await bitsTransaction;

    const response = await fetch(
      extensionUri + '/redeem', {
        method: "POST",
        headers: {
          'Content-Type': 'application/json',
          Authorization: authorization
        },
        body: JSON.stringify({"redeem": redeem, "transaction": tx})
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


// document.body.addEventListener('', async function (evt: any) {
// 	console.log('tangia:buyTwitchProduct', evt.detail);
// 	try {
// 		window.document.body.classList.add('opacity-50');
// 		// segment?.track("Ext Purchase Started", { interaction: i, interactionInfo, buyerVars });
// 		const bitsTransaction = new Promise<object>((complete, cancel) => {
// 			Twitch.ext.bits.onTransactionComplete(complete);
// 			Twitch.ext.bits.onTransactionCancelled(cancel);
// 		});
// 		Twitch.ext.bits.useBits(evt.detail.ProductID);
// 		// this contains the signed JWT of the buy transaction
// 		const tx = await bitsTransaction;
// 		htmx.trigger(window.document.body, 'tangia:purchaseCompleted', { ...evt.detail, ...tx });
// 		// segment?.track("Ext Purchase Completed", { interaction: i, interactionInfo, buyerVars, product: p });
// 	} catch (e: any) {
// 		htmx.trigger(window.document.body, 'tangia:purchaseCancelled', { ...evt.detail, ...e });

// 		// segment?.track("Ext Purchase Failed", { interaction: i, interactionInfo, buyerVars, error: e });
// 	} finally {
// 		window.document.body.classList.remove('opacity-50');
// 		Twitch.ext.bits.onTransactionComplete(() => {});
// 		Twitch.ext.bits.onTransactionCancelled(() => {});
// 	}
// });
