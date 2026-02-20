export const toast: any = (msg: string) => {
  try {
    // Minimal non-blocking toast: console.log + non-intrusive DOM update
    console.log('[toast]', msg)
    // create a temporary floating element
    const el = document.createElement('div')
    el.textContent = msg
    el.style.position = 'fixed'
    el.style.right = '20px'
    el.style.top = '20px'
    el.style.background = '#111'
    el.style.color = '#fff'
    el.style.padding = '8px 12px'
    el.style.border = '1px solid #333'
    el.style.borderRadius = '6px'
    el.style.zIndex = '9999'
    document.body.appendChild(el)
    setTimeout(() => document.body.removeChild(el), 3000)
  } catch (e) {
    // fallback
    alert(msg)
  }
}

toast.error = (msg: string) => toast(`Error: ${msg}`)
toast.success = (msg: string) => toast(`Success: ${msg}`)
toast.info = (msg: string) => toast(`Info: ${msg}`)

export default toast
