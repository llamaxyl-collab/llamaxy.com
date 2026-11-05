// llamaxy.com checkout (Apo 4 Nov 2026): basket → Stripe Checkout session. Prices and stock come from
// llamaxy.com/prices.json (built hourly from our FBA stock), never from the browser; max 3 per product.
// Secrets: STRIPE_TEST, STRIPE_LIVE. Live payments when var LIVE = "1" (on since Apo 5 Nov 2026).
const SITE = 'https://llamaxy.com/'
const H = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'content-type', 'Content-Type': 'application/json' }
const out = (o, status = 200) => new Response(JSON.stringify(o), { status, headers: H })

export default {
  async fetch(req, env) {
    if (req.method === 'OPTIONS') return new Response(null, { headers: H })
    if (req.method !== 'POST') return out({ error: 'POST only' }, 405)
    const { items, test, base, email, addr } = await req.json().catch(() => ({}))
    const key = test ? env.STRIPE_TEST : env.LIVE === '1' && env.STRIPE_LIVE
    if (!key) return out({ error: 'Our payment service is temporarily unavailable. You have not been charged.' }, 503)
    const back = typeof base === 'string' && base.startsWith(SITE) ? base : SITE
    if (!Array.isArray(items) || !items.length || items.length > 12) return out({ error: 'Your basket can hold up to 12 different items.' }, 400)
    const prices = await (await fetch(SITE + 'prices.json', { cf: { cacheTtl: 60 } })).json()
    const lines = []
    for (const x of items) {
      const p = prices[x.a], q = Number(x.q)
      if (!p) return out({ error: 'Sorry, an item in your basket has just sold out. Please remove it and try again.' }, 409)
      if (!Number.isInteger(q) || q < 1 || q > 3) return out({ error: 'Maximum 3 of each item per order.' }, 400)
      lines.push({ a: x.a, q, p: p.p, t: p.t, i: p.i })
    }
    // Max 3 of each item per customer over 30 days (Apo 5 Nov 2026), by the email given before payment;
    // the order loop on our server checks the delivery address as well
    const mail = typeof email === 'string' ? email.trim().toLowerCase() : ''
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(mail)) return out({ error: 'Please enter a valid email address.' }, 400)
    // the delivery address is taken here, before payment (Apo 5 Nov 2026: "iptal etmeden önce olmuyor mu"), so the
    // same house with another email is stopped before anyone pays
    const a = addr && typeof addr === 'object' ? addr : {}
    const t = (v, n) => (typeof v === 'string' ? v.trim().slice(0, n) : '')
    const ad = { n: t(a.n, 80), l1: t(a.l1, 100), l2: t(a.l2, 100), c: t(a.c, 60), pc: t(a.pc, 10).toUpperCase() }
    if (!ad.n || !ad.l1 || !ad.c || !/^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$/.test(ad.pc)) return out({ error: 'Please enter your full name and UK delivery address (with a valid postcode).' }, 400)
    // same house = postcode + house number ("1 High Street" = "1 High St."); no number → first word ("Rose Cottage")
    const home = (x) => `${(x.pc || '').replace(/\s/g, '').toUpperCase()}|${((x.l1 || '').match(/\d+[a-z]?/i)?.[0] ?? (x.l1 || '').split(/[\s,]+/)[0]).toLowerCase()}`
    const since = Math.floor(Date.now() / 1000) - 30 * 86400
    const had = {}
    let after = ''
    for (let page = 0; page < 5; page++) { // all paid sessions of the last 30 days (a small shop: a page or two)
      const r = await (await fetch(`https://api.stripe.com/v1/checkout/sessions?status=complete&limit=100&created[gte]=${since}${after}`, { headers: { Authorization: 'Bearer ' + key } })).json()
      for (const s of r.data ?? []) {
        if (s.payment_status !== 'paid') continue
        const same = (s.customer_details?.email || '').toLowerCase() === mail || (s.metadata?.addr && home(JSON.parse(s.metadata.addr)) === home(ad))
        if (same) for (const x of JSON.parse(s.metadata?.items || '[]')) had[x.a] = (had[x.a] ?? 0) + x.q
      }
      if (!r.has_more || !r.data?.length) break
      after = `&starting_after=${r.data[r.data.length - 1].id}`
    }
    for (const x of lines) if ((had[x.a] ?? 0) + x.q > 3)
      return out({ error: `You can buy up to 3 of each item${had[x.a] ? ` — you have already ordered ${had[x.a]} of “${x.t.slice(0, 60)}” recently` : ''}. Want more? Please contact us at info@llamaxy.com.` }, 409)
    // Before payment, our server asks Amazon: stock for every item + will it deliver to this address (Apo 5 Nov 2026:
    // "ödeme alıp iade etmeyelim, öncesinde kontrol edelim"). Server down / slow = let the order through; the order
    // loop still refunds if Amazon refuses later.
    const chk = await fetch('https://apozone-ebay.taildd5476.ts.net/shop/check', { method: 'POST', headers: { 'content-type': 'application/json', 'x-shop-secret': env.SHOP_CHECK || '' }, body: JSON.stringify({ items: lines.map((x) => ({ a: x.a, q: x.q })), addr: ad }), signal: AbortSignal.timeout(12000) }).then((r) => (r.ok ? r.json() : null)).catch(() => null)
    if (chk && chk.ok === false) {
      const t = lines.find((x) => x.a === chk.asin)?.t
      return out({ error: chk.reason === 'stock' ? `Sorry, “${(t || 'an item in your basket').slice(0, 60)}” has just sold out. Please remove it and try again. You have not been charged.` : 'Sorry, we cannot deliver to this address. Please check it, or contact us at info@llamaxy.com. You have not been charged.' }, 409)
    }
    const sub = lines.reduce((n, x) => n + x.p * x.q, 0)
    const f = {
      mode: 'payment', locale: 'en-GB', customer_email: mail, 'adaptive_pricing[enabled]': 'false', // always GBP (4 Nov: OVH FR IP showed EUR +4% fee)
      success_url: back + 'thanks.html', cancel_url: back + 'basket.html',
      'payment_intent_data[shipping][name]': ad.n,
      'payment_intent_data[shipping][address][line1]': ad.l1,
      'payment_intent_data[shipping][address][line2]': ad.l2,
      'payment_intent_data[shipping][address][city]': ad.c,
      'payment_intent_data[shipping][address][postal_code]': ad.pc,
      'payment_intent_data[shipping][address][country]': 'GB',
      'metadata[addr]': JSON.stringify(ad),
      'phone_number_collection[enabled]': 'true',
      'shipping_options[0][shipping_rate_data][display_name]': 'Standard UK delivery (1–2 working days to dispatch)',
      'shipping_options[0][shipping_rate_data][type]': 'fixed_amount',
      'shipping_options[0][shipping_rate_data][fixed_amount][amount]': String(sub >= 40 ? 0 : 399),
      'shipping_options[0][shipping_rate_data][fixed_amount][currency]': 'gbp',
      'metadata[items]': JSON.stringify(lines.map(({ a, q, p }) => ({ a, q, p }))),
    }
    lines.forEach((x, i) => {
      f[`line_items[${i}][quantity]`] = String(x.q)
      f[`line_items[${i}][price_data][currency]`] = 'gbp'
      f[`line_items[${i}][price_data][unit_amount]`] = String(Math.round(x.p * 100))
      f[`line_items[${i}][price_data][product_data][name]`] = x.t
      if (x.i) f[`line_items[${i}][price_data][product_data][images][0]`] = SITE + x.i
    })
    const r = await fetch('https://api.stripe.com/v1/checkout/sessions', {
      method: 'POST', body: new URLSearchParams(f),
      headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    const j = await r.json()
    if (!r.ok) return out({ error: 'Payment could not be started. You have not been charged — please try again.' }, 502)
    return out({ url: j.url })
  },
}
