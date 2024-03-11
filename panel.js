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

async function getLayout(layout) {
  console.debug("layout")
  const response = await fetch(
    extensionUri + `/layouts/${layout}`, {
      method: "GET",
    }
  )

  const layout_resp = await response.json()
  console.debug(layout_resp)
  return layout_resp
}

async function renderLayout () {

  const layout = getLayout(1)

  const elements = layout["elements"]
  let webhooks = []
  const panelTitle = document.getElementById('panelTitle')
  panelTitle.innerHTML = layout["layout"]["title"]
  const mainPanel = document.getElementById('mainPanel')
  let pannelInner = ""
  for (const index in elements){

    const element = elements[index]
    console.log(element)
    const element_type = element["type"]
    console.log(element_type)
    if (element_type == "image") {
      const element_id = element["id"]
      pannelInner += `<div><img src="${extensionUri}/image/${element_id}"></div>`
    }
    if (element_type == "text") {
      const text = element["text"]["text"]
      pannelInner += `<div><p>${text}</p></div>`
    }
    if (element_type == "webhook") {
      const text = element["webhook"]["text"]
      pannelInner += `<div><button id="element${index}">1 <img src="bit.gif" width="28" height="28"> ${text} </button></div>`
      webhooks.push({
        "html_id": `element${index}`,
        "element": element,
      })
    }
  }

  mainPanel.innerHTML = pannelInner
  for (const index in webhooks){
    const webhook = webhooks[index]
    console.log(webhook)
    const webhookElement = document.getElementById(webhook["html_id"])
    const webhookID = webhook["element"]["webhook"]["id"]
    console.log(webhookID)
    const webhookBitsProduct = webhook["element"]["webhook"]["bits_product"]
    console.log(webhookBitsProduct)
    webhookElement.addEventListener(
      "click",
      async function () {
        webhookRedeem(webhookID, webhookBitsProduct)
      },
      false,
    )
  }

}


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
      extensionUri + '/webhook', {
        method: "POST",
        headers: {
          'Content-Type': 'application/json',
          Authorization: authorization
        },
        body: JSON.stringify({"webhook_id": webhookID, "transaction": tx})
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
