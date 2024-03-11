'use strict'
import { twitch, extensionUri } from './globals.js'

let authorization

twitch.onAuthorized(function (auth) {
  authorization = 'Bearer ' + auth.token
  console.log('bits enabled: ' + twitch.features.isBitsEnabled)
})


// add the auth token to the request as a header
htmx.on("htmx:configRequest", (e)=> {
  e.detail.headers["Authorization"] = authorization
})

// twitch.onAuthorized(function (auth) {
//   authorization = 'Bearer ' + auth.token
//   getLayoutList().then((layoutList) => {
//     console.log(layoutList)
//     for (const layout of layoutList.layouts) {
//         const newOption = document.createElement('option')
//         console.log(layout)
//         newOption.value = layout.id
//         newOption.text = layout.name
//         document.getElementById('layout_select').appendChild(newOption)
//     }
//   }).catch(function (error) {
//     console.error(error)
//   })
// })

// async function getLayoutList () {
//     const layoutsUrl = extensionUri + '/layouts'

//     // get list of a channel's layouts using the EBS
//     const response = await fetch(layoutsUrl, {
//         method: 'GET',
//         headers: {
//         'Content-Type': 'application/json',
//         Authorization: authorization
//         }
//     })

//     if (!response.ok) {
//         return await response.text().then(text => {
//         const errorMessage = 'could not get layouts: ' + response.status + ' ' + text
//         throw new Error(errorMessage)
//         })
//     }

//     const layouts = await response.json()
//     return layouts
// }

