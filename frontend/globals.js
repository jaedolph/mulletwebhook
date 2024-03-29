// Global vars

export const twitch = window.Twitch.ext
const params = new URLSearchParams(window.location.search)
const state = params.get('state')
export let extensionUri = 'https://mulletwebhook.jaedolph.net'
if (state === 'testing') {
  extensionUri = 'https://mulletwebhook-test.hv1.jaedolph.net'
}
