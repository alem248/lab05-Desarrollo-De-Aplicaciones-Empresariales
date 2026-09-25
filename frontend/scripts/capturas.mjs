/**
 * Capturas del entregable - paso 11.
 *
 * Genera las capturas que pide el enunciado en documento/capturas/:
 *
 *   01  las cuatro operaciones del panel (paso 4)
 *   02  listado de peliculas con list_display, list_filter y buscador (paso 5)
 *   03  el buscador del paso 5 buscando por nombre de persona
 *   04  formulario de la pelicula con el inline y la auditoria en solo
 *       lectura (pasos 6 y 7)
 *   05  la MISMA ficha como editor del grupo "editores" (sin boton de eliminar)
 *   06  el listado del editor, sin la accion masiva de eliminar
 *   07  la vista publica de recomendaciones en React (paso 10)
 *   08  la vista publica filtrada por un genero
 *   09  el detalle con las valoraciones de la pelicula
 *
 * Requisitos: el backend de Django en marcha con los datos del paso 8.
 *
 *   cd backend
 *   py manage.py migrate
 *   py manage.py seed_movies
 *   py manage.py setup_editores --reset-password
 *   py manage.py createsuperuser        # si aun no existe
 *   py manage.py runserver 8000
 *
 * Y, en otra terminal, el frontend:
 *
 *   cd frontend
 *   npm install
 *   npm run dev
 *
 * Despues, desde frontend/:
 *
 *   node scripts/capturas.mjs
 *
 * Las credenciales se pueden cambiar con las variables de entorno
 * SUPERUSUARIO, PASSWORD_SUPERUSUARIO, EDITOR y PASSWORD_EDITOR.
 */

import { chromium } from 'playwright'
import { mkdir } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const aqui = dirname(fileURLToPath(import.meta.url))
const raiz = resolve(aqui, '..')
const salida = resolve(raiz, '..', 'documento', 'capturas')

const BASE = process.env.BASE_URL || 'http://127.0.0.1:8000'
const FRONTEND = process.env.FRONTEND_URL || 'http://localhost:5173'

const SUPERUSUARIO = process.env.SUPERUSUARIO || 'alem248'
const PASSWORD_SUPERUSUARIO = process.env.PASSWORD_SUPERUSUARIO || 'Cinevault2026!'
const EDITOR = process.env.EDITOR || 'editor01'
const PASSWORD_EDITOR = process.env.PASSWORD_EDITOR || 'Editor2026!'

// 1600x1000: con el menu lateral desplegado, el panel necesita ese ancho para
// que se vean todas las columnas de list_display.
const VIEWPORT = { width: 1600, height: 1000 }

async function capturar(page, nombre) {
  await page.screenshot({ path: resolve(salida, `${nombre}.png`), fullPage: true })
  console.log(`  ${nombre}.png`)
}

/**
 * Abre una pestana nueva, en un contexto limpio, con la sesion iniciada.
 *
 * Hace falta un contexto por usuario: si se reutiliza el mismo, al pedir
 * /admin/login/ con una sesion ya abierta Django redirige al panel y el
 * formulario de acceso nunca llega a aparecer.
 */
async function abrirComo(navegador, usuario, clave) {
  const contexto = await navegador.newContext({ viewport: VIEWPORT, locale: 'es-PE' })
  const page = await contexto.newPage()

  await page.goto(`${BASE}/admin/login/?next=/admin/`, { waitUntil: 'domcontentloaded' })
  await page.fill('#id_username', usuario)
  await page.fill('#id_password', clave)
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'domcontentloaded' }),
    page.click('input[type="submit"]'),
  ])

  // El encabezado solo incluye el formulario de cierre de sesion si la sesion
  // esta iniciada. Ojo: el nombre se ve en mayusculas por CSS, pero en el DOM
  // conserva las minusculas con las que se escribio.
  const cerrado = await page.$('#logout-form')
  const nombre = await page.textContent('#user-tools')
  if (!cerrado || !nombre?.toLowerCase().includes(usuario.toLowerCase())) {
    throw new Error(`No se pudo iniciar sesion como ${usuario}`)
  }
  console.log(`  sesion iniciada como ${usuario}`)
  return page
}

async function main() {
  await mkdir(salida, { recursive: true })
  console.log(`Capturas en ${salida}\n`)

  const navegador = await chromium.launch()
  let admin = null
  let editor = null

  try {
    // --- Paso 4: las cuatro operaciones, sin ninguna vista escrita ---
    console.log('superusuario')
    admin = await abrirComo(navegador, SUPERUSUARIO, PASSWORD_SUPERUSUARIO)
    await capturar(admin, '01-admin-cuatro-operaciones')

    // --- Paso 5: list_display, list_filter y search_fields ---
    await admin.goto(`${BASE}/admin/movies/movie/`, { waitUntil: 'domcontentloaded' })
    await capturar(admin, '02-admin-listado-peliculas-personalizado')

    // El buscador buscando por nombre de persona, no por titulo.
    await admin.fill('#searchbar', 'Villeneuve')
    await admin.click('#changelist-search input[type="submit"]')
    await admin.waitForLoadState('domcontentloaded')
    await capturar(admin, '03-admin-buscador-por-nombre-de-persona')

    // --- Pasos 6 y 7: inline de valoraciones y auditoria en solo lectura ---
    // getAttribute devuelve la ruta relativa tal cual aparece en el HTML, hay
    // que resolverla contra la base antes de navegar.
    const href = await admin.getAttribute('#result_list tbody tr th.field-title a', 'href')
    const ficha = new URL(href, BASE).href
    await admin.goto(ficha, { waitUntil: 'domcontentloaded' })
    await capturar(admin, '04-admin-formulario-con-inline-y-auditoria')

    // --- Paso 9: la misma ficha, ahora como editor ---
    console.log('editor del grupo "editores"')
    editor = await abrirComo(navegador, EDITOR, PASSWORD_EDITOR)
    await editor.goto(ficha, { waitUntil: 'domcontentloaded' })
    await capturar(editor, '05-comparacion-editor-sin-borrar')

    await editor.goto(`${BASE}/admin/movies/movie/`, { waitUntil: 'domcontentloaded' })
    await capturar(editor, '06-comparacion-editor-listado-sin-borrado-masivo')

    // --- Paso 10: la vista publica en React ---
    console.log('vista publica (React)')
    const publico = await (await navegador.newContext({ viewport: VIEWPORT, locale: 'es-PE' })).newPage()
    await publico.goto(FRONTEND, { waitUntil: 'networkidle' })
    await publico.waitForSelector('.tarjeta', { timeout: 20000 })
    await capturar(publico, '07-vista-publica-recomendaciones')

    // Filtrando por genero: la recomendacion "del mismo genero".
    const opciones = await publico.$$eval('#selector-genero option', (os) =>
      os.map((o) => ({ valor: o.value, texto: o.textContent })),
    )
    const ficcion = opciones.find((o) => /ciencia/i.test(o.texto))
    if (ficcion) {
      await publico.selectOption('#selector-genero', ficcion.valor)
      await publico.waitForTimeout(1500)
      await capturar(publico, '08-vista-publica-filtrada-por-genero')
    }

    // El detalle con las valoraciones de la pelicula.
    await publico.click('.tarjeta-boton')
    await publico.waitForSelector('.detalle', { timeout: 20000 })
    await capturar(publico, '09-vista-publica-detalle-con-valoraciones')

    console.log('\nListo.')
  } finally {
    await navegador.close()
  }
}

main().catch((error) => {
  console.error('\nError:', error.message)
  console.error(
    '\nComprueba que el backend esta en marcha (py manage.py runserver 8000),\n' +
      'que los datos estan cargados (py manage.py seed_movies) y que el grupo\n' +
      '"editores" existe (py manage.py setup_editores --reset-password).',
  )
  process.exit(1)
})
