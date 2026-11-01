/* Dashboard: exportaciones peruanas de café, cacao y madera a la UE (EUDR).
   Lee data/datos.json (generado por 02_procesar_datos.ipynb) y data/hallazgos.json (03_analisis.ipynb). */
(() => {
  "use strict";

  const VARS_PRODUCTO = ["--cafe", "--cacao", "--madera"];
  const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre"];
  const nf0 = new Intl.NumberFormat("es-PE", { maximumFractionDigits: 0 });
  const nf1 = new Intl.NumberFormat("es-PE", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const nf2 = new Intl.NumberFormat("es-PE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  let D = null;          // datos
  let HALLAZGOS = [];
  const estado = { producto: -1, anio: null, periodo: "anual", indicador: "fob", ambito: "ue", desde: 2012, hasta: null };
  let ordenTabla = { col: "fob", desc: true };
  let filasTabla = [];

  // ---------- utilidades ----------
  const $ = (id) => document.getElementById(id);
  const css = (nombre) => getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
  const colorProducto = (p) => css(VARS_PRODUCTO[p]);

  function fmtFOB(v) {
    const m = v / 1e6;
    return "US$ " + (Math.abs(m) >= 100 ? nf0.format(m) : nf1.format(m)) + " M";
  }
  function fmtPeso(kg) {
    const t = kg / 1000;
    if (Math.abs(t) >= 10000) return nf1.format(t / 1000) + " mil t";
    return nf0.format(t) + " t";
  }
  const fmtValor = (v, ind) => (ind === "fob" ? fmtFOB(v) : fmtPeso(v));
  // Versión para tarjetas KPI: la unidad va en tamaño menor
  const unidadPequena = (texto) => texto.replace(/^US\$ /, "<small>US$</small> ").replace(/ (M|mil t|t)$/, " <small>$1</small>");

  // Etiquetas cortas para la escala logarítmica del mapa
  function fmtCorto(v, ind) {
    if (ind === "fob") {
      if (v >= 1e9) return "$" + nf1.format(v / 1e9) + " mil M";
      if (v >= 1e6) return "$" + nf0.format(v / 1e6) + " M";
      if (v >= 1e3) return "$" + nf0.format(v / 1e3) + " mil";
      return "$" + nf0.format(v);
    }
    if (v >= 1e6) return nf0.format(v / 1e6) + " mil t";
    if (v >= 1e3) return nf0.format(v / 1e3) + " t";
    return nf0.format(v) + " kg";
  }
  const fmtPct = (v) => (isFinite(v) ? nf1.format(v) + " %" : "—");
  const nombreIndicador = (ind) => (ind === "fob" ? "valor FOB" : "volumen (peso neto)");

  function delta(actual, previo, sufijo = "%") {
    if (!isFinite(actual) || !isFinite(previo) || previo === 0) return "";
    const d = sufijo === "%" ? (actual / previo - 1) * 100 : actual - previo;
    const clase = d >= 0 ? "delta-sube" : "delta-baja";
    const signo = d >= 0 ? "▲ +" : "▼ ";
    return `<span class="${clase}">${signo}${nf1.format(d)} ${sufijo === "%" ? "%" : "p.p."}</span>`;
  }

  const esParcial = (anio) => anio === D.meta.anio_parcial;
  const periodoEfectivo = (anio) => (esParcial(anio) ? "parcial" : estado.periodo);
  const textoPeriodo = () => `enero–${MESES[D.meta.ultimo_mes - 1]}`;
  const etiquetaPeriodo = (anio) => (periodoEfectivo(anio) === "parcial" ? `${anio} (${textoPeriodo()})` : String(anio));

  // valor de una fila anual [anio, p, iso3, fob, kg, fob_p, kg_p] según indicador y periodo
  function valorFila(f, ind, per) {
    if (per === "parcial") return ind === "fob" ? f[5] : f[6];
    return ind === "fob" ? f[3] : f[4];
  }
  const productoIncluido = (p) => estado.producto === -1 || estado.producto === p;
  const esUE = (iso) => (D.paises[iso] ? D.paises[iso][1] === 1 : false);
  const nombrePais = (iso) => (D.paises[iso] ? D.paises[iso][0] : iso);

  // índice: anio -> filas
  let porAnio = new Map();
  function indexar() {
    porAnio = new Map();
    for (const f of D.anual) {
      if (!porAnio.has(f[0])) porAnio.set(f[0], []);
      porAnio.get(f[0]).push(f);
    }
  }

  // Agrega por país para un año: Map iso -> {fob, kg}
  function porPais(anio, per, filtroProducto = productoIncluido) {
    const m = new Map();
    for (const f of porAnio.get(anio) || []) {
      if (!filtroProducto(f[1])) continue;
      const o = m.get(f[2]) || { fob: 0, kg: 0 };
      o.fob += valorFila(f, "fob", per);
      o.kg += valorFila(f, "kg", per);
      m.set(f[2], o);
    }
    return m;
  }

  // Totales UE / resto para un año y filtro de producto
  function totales(anio, per, filtroProducto = productoIncluido) {
    const t = { ue: { fob: 0, kg: 0 }, resto: { fob: 0, kg: 0 } };
    for (const [iso, v] of porPais(anio, per, filtroProducto)) {
      const b = esUE(iso) ? t.ue : t.resto;
      b.fob += v.fob;
      b.kg += v.kg;
    }
    t.mundo = { fob: t.ue.fob + t.resto.fob, kg: t.ue.kg + t.resto.kg };
    return t;
  }

  function aniosSerie() {
    const anios = [];
    for (let a = estado.desde; a <= estado.hasta; a++) {
      if (estado.periodo === "anual" && esParcial(a)) continue;
      anios.push(a);
    }
    return anios;
  }

  // ---------- Plotly: estilo común ----------
  function layoutBase(extra = {}) {
    const base = {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { family: css("--font") || "system-ui, sans-serif", color: css("--text-secondary"), size: 12 },
      margin: { l: 56, r: 16, t: 8, b: 36 },
      hoverlabel: { bgcolor: css("--surface-1"), bordercolor: css("--axis"), font: { color: css("--text-primary"), size: 13 } },
      xaxis: { showgrid: false, linecolor: css("--axis"), tickcolor: css("--axis"), zeroline: false, fixedrange: true },
      yaxis: { gridcolor: css("--grid"), zeroline: false, linecolor: css("--axis"), fixedrange: true, rangemode: "tozero" },
      showlegend: false,
    };
    return Object.assign(base, extra);
  }
  const CONFIG = { displayModeBar: false, responsive: true };

  function leyenda(contenedor, items) {
    $(contenedor).innerHTML = items
      .map((it) => `<span><i class="punto" style="background:${it.color};opacity:${it.opacidad ?? 1}"></i>${it.nombre}</span>`)
      .join("");
  }

  // ---------- Controles ----------
  function segmentado(idContenedor, opciones, clave, alCambiar) {
    const cont = $(idContenedor);
    cont.innerHTML = "";
    for (const op of opciones) {
      const b = document.createElement("button");
      b.type = "button";
      b.dataset.valor = String(op.valor);
      b.innerHTML = (op.color ? `<i class="punto" style="background:${op.color}"></i>` : "") + op.texto;
      b.addEventListener("click", () => {
        if (b.disabled) return;
        estado[clave] = op.valor;
        marcar(idContenedor, clave);
        alCambiar();
      });
      cont.appendChild(b);
    }
    marcar(idContenedor, clave);
  }
  function marcar(idContenedor, clave) {
    for (const b of $(idContenedor).querySelectorAll("button")) {
      b.setAttribute("aria-pressed", String(b.dataset.valor === String(estado[clave])));
    }
  }

  function construirControles() {
    const opcionesProducto = [{ valor: -1, texto: "Los tres" }].concat(
      D.productos.map((n, i) => ({ valor: i, texto: n, color: colorProducto(i) }))
    );
    segmentado("f-producto", opcionesProducto, "producto", render);
    segmentado("f-periodo", [{ valor: "anual", texto: "Año completo" }, { valor: "parcial", texto: textoPeriodo()[0].toUpperCase() + textoPeriodo().slice(1) }], "periodo", () => { ajustarRango(); render(); });
    segmentado("f-indicador", [{ valor: "fob", texto: "Valor FOB" }, { valor: "kg", texto: "Volumen" }], "indicador", render);
    segmentado("f-ambito", [{ valor: "ue", texto: "UE-27" }, { valor: "mundo", texto: "Mundo" }], "ambito", render);

    const anios = [];
    for (let a = D.meta.anio_min; a <= D.meta.anio_max; a++) anios.push(a);
    $("f-anio").innerHTML = anios.slice().reverse().map((a) => `<option value="${a}">${a}${esParcial(a) ? " (ene–" + MESES[D.meta.ultimo_mes - 1].slice(0, 3) + ")" : ""}</option>`).join("");
    $("f-anio").value = String(estado.anio);
    $("f-anio").addEventListener("change", (e) => {
      estado.anio = Number(e.target.value);
      if (esParcial(estado.anio) && estado.periodo === "anual") {
        estado.periodo = "parcial";  // así la serie también llega al año parcial
        ajustarRango();
      }
      render();
    });

    $("f-desde").innerHTML = anios.map((a) => `<option value="${a}">${a}</option>`).join("");
    $("f-hasta").innerHTML = anios.map((a) => `<option value="${a}">${a}</option>`).join("");
    $("f-desde").value = String(estado.desde);
    $("f-hasta").value = String(estado.hasta);
    $("f-desde").addEventListener("change", (e) => {
      estado.desde = Math.min(Number(e.target.value), estado.hasta - 1);
      $("f-desde").value = String(estado.desde);
      render();
    });
    $("f-hasta").addEventListener("change", (e) => {
      estado.hasta = Math.max(Number(e.target.value), estado.desde + 1);
      $("f-hasta").value = String(estado.hasta);
      render();
    });
  }

  // Con "Año completo" la serie no puede incluir el año parcial
  function ajustarRango() {
    const maximo = estado.periodo === "anual" ? D.meta.anio_parcial - 1 : D.meta.anio_max;
    if (estado.hasta > maximo || estado.hasta === D.meta.anio_parcial - 1 || estado.hasta === D.meta.anio_max) estado.hasta = maximo;
    $("f-hasta").value = String(estado.hasta);
  }

  function actualizarAvisoPeriodo() {
    const botonAnual = $("f-periodo").querySelector('button[data-valor="anual"]');
    if (esParcial(estado.anio)) {
      botonAnual.disabled = true;
      botonAnual.title = `${estado.anio} solo tiene datos hasta ${MESES[D.meta.ultimo_mes - 1]}`;
      $("aviso-periodo").textContent = `${estado.anio} tiene datos hasta ${MESES[D.meta.ultimo_mes - 1]}: los indicadores comparan ${textoPeriodo()} de ${estado.anio} con el mismo periodo de ${estado.anio - 1}.`;
    } else {
      botonAnual.disabled = false;
      botonAnual.title = "";
      $("aviso-periodo").textContent = estado.periodo === "parcial"
        ? `Todos los años se miden en ${textoPeriodo()}, para compararlos con ${D.meta.anio_parcial}.`
        : `Años completos (la serie llega hasta ${D.meta.anio_parcial - 1}). Elige “${textoPeriodo()}” para incluir ${D.meta.anio_parcial}.`;
    }
    for (const b of $("f-periodo").querySelectorAll("button")) {
      const activo = b.dataset.valor === periodoEfectivo(estado.anio);
      b.setAttribute("aria-pressed", String(activo));
    }
  }

  // ---------- KPIs ----------
  function renderKPIs() {
    const per = periodoEfectivo(estado.anio);
    const ind = estado.indicador;
    const t = totales(estado.anio, per);
    const tPrev = totales(estado.anio - 1, per);
    const partUE = (t.ue[ind] / t.mundo[ind]) * 100;
    const partUEPrev = (tPrev.ue[ind] / tPrev.mundo[ind]) * 100;

    const paises = [...porPais(estado.anio, per)].filter(([iso]) => esUE(iso)).sort((a, b) => b[1][ind] - a[1][ind]);
    const lider = paises[0];
    const nDestinos = paises.filter(([, v]) => v[ind] > 0).length;

    const totUE = D.total_ue.find((r) => r[0] === estado.anio);
    const totalPeruUE = totUE ? (per === "parcial" ? totUE[2] : totUE[1]) : NaN;
    const pesoEnUE = (t.ue.fob / totalPeruUE) * 100;

    const nombreProd = estado.producto === -1 ? "café, cacao y madera" : D.productos[estado.producto].toLowerCase();
    const etq = etiquetaPeriodo(estado.anio);

    const tarjetas = [
      { titulo: `Exportado a la UE-27 · ${etq}`, valor: unidadPequena(fmtFOB(t.ue.fob)), detalle: `${delta(t.ue.fob, tPrev.ue.fob)} vs ${estado.anio - 1}` },
      { titulo: `Volumen a la UE-27 · ${etq}`, valor: unidadPequena(fmtPeso(t.ue.kg)), detalle: `${delta(t.ue.kg, tPrev.ue.kg)} vs ${estado.anio - 1}` },
      { titulo: `Parte que va a la UE (${ind === "fob" ? "FOB" : "volumen"})`, valor: fmtPct(partUE), detalle: `${delta(partUE, partUEPrev, "pp")} · resto: ${fmtPct(100 - partUE)}` },
      {
        titulo: "Principal destino en la UE",
        valor: lider ? nombrePais(lider[0]) : "—",
        detalle: lider ? `${fmtPct((lider[1][ind] / t.ue[ind]) * 100)} de lo enviado a la UE · ${nDestinos} países UE` : "",
      },
      { titulo: "Peso en todo lo que Perú vende a la UE", valor: fmtPct(pesoEnUE), detalle: `${nombreProd} sobre el total FOB a la UE-27` },
    ];
    if (estado.producto === -1) {
      tarjetas.push({ titulo: "Valor unitario", valor: "—", detalle: "Elige un producto para comparar US$/kg (UE vs. resto)" });
    } else {
      const vuUE = t.ue.fob / t.ue.kg;
      const vuResto = t.resto.fob / t.resto.kg;
      tarjetas.push({
        titulo: "Valor unitario a la UE",
        valor: isFinite(vuUE) ? `${nf2.format(vuUE)} <small>US$/kg</small>` : "—",
        detalle: isFinite(vuResto) ? `Resto del mundo: ${nf2.format(vuResto)} US$/kg` : "",
      });
    }
    $("kpis").innerHTML = tarjetas
      .map((k) => `<div class="kpi"><div class="titulo">${k.titulo}</div><div class="valor">${k.valor}</div><div class="detalle">${k.detalle}</div></div>`)
      .join("");
  }

  // ---------- Mapa ----------
  let colaMapa = Promise.resolve();
  function renderMapa() {
    const per = periodoEfectivo(estado.anio);
    const ind = estado.indicador;
    const datos = [...porPais(estado.anio, per)]
      .filter(([iso, v]) => v[ind] > 0 && iso.length === 3 && !iso.startsWith("X") && (estado.ambito === "mundo" || esUE(iso)));
    const total = datos.reduce((s, [, v]) => s + v[ind], 0);
    const z = datos.map(([, v]) => Math.log10(v[ind]));
    const zmin = Math.floor(Math.min(...z, 6));
    const zmax = Math.ceil(Math.max(...z, zmin + 1));
    const ticks = [];
    for (let k = zmin; k <= zmax; k++) ticks.push(k);
    const etiquetaTick = (k) => fmtCorto(10 ** k, ind);

    const traza = {
      type: "choropleth",
      locationmode: "ISO-3",
      locations: datos.map(([iso]) => iso),
      z,
      zmin,
      zmax,
      text: datos.map(([iso, v]) => `<b>${nombrePais(iso)}</b>${esUE(iso) ? " · UE" : ""}<br>${fmtValor(v[ind], ind)}<br>${fmtPct((v[ind] / total) * 100)} del total mostrado`),
      hovertemplate: "%{text}<extra></extra>",
      colorscale: [[0, css("--seq-100")], [0.33, css("--seq-250")], [0.6, css("--seq-400")], [0.8, css("--seq-550")], [1, css("--seq-700")]],
      marker: { line: { color: css("--surface-1"), width: 0.6 } },
      colorbar: {
        thickness: 10, len: 0.7, outlinewidth: 0,
        tickvals: ticks, ticktext: ticks.map(etiquetaTick),
        tickfont: { color: css("--text-secondary"), size: 11 },
      },
    };
    const geo = {
      scope: estado.ambito === "ue" ? "europe" : "world",
      projection: { type: estado.ambito === "ue" ? "mercator" : "natural earth" },
      showframe: false,
      showcoastlines: false,
      showland: true,
      landcolor: css("--surface-2"),
      showcountries: true,
      countrycolor: css("--grid"),
      showocean: false,
      bgcolor: "rgba(0,0,0,0)",
      lataxis: estado.ambito === "ue" ? { range: [34, 71] } : undefined,
      lonaxis: estado.ambito === "ue" ? { range: [-12, 35] } : undefined,
    };
    // El mapa carga su topojson de forma asíncrona: se encolan los redibujos para que un clic rápido no pise al anterior
    const layout = layoutBase({ geo, margin: { l: 0, r: 0, t: 0, b: 0 }, dragmode: false });
    colaMapa = colaMapa.then(() => Plotly.react("g-mapa", [traza], layout, CONFIG)).catch((e) => console.warn("Mapa:", e));

    const prod = estado.producto === -1 ? "Café, cacao y madera" : D.productos[estado.producto];
    $("t-mapa").textContent = `${prod}: destinos ${estado.ambito === "ue" ? "en la UE-27" : "en el mundo"}, ${etiquetaPeriodo(estado.anio)}`;
    $("s-mapa").textContent = `Color según ${nombreIndicador(ind)} (escala logarítmica). Países sin envíos en gris claro. Pasa el cursor para ver el detalle.`;
  }

  // ---------- Top destinos UE ----------
  function renderTop() {
    const per = periodoEfectivo(estado.anio);
    const ind = estado.indicador;
    const ue = [...porPais(estado.anio, per)].filter(([iso, v]) => esUE(iso) && v[ind] > 0).sort((a, b) => b[1][ind] - a[1][ind]);
    const totalUE = ue.reduce((s, [, v]) => s + v[ind], 0);
    const top = ue.slice(0, 10).reverse();
    const traza = {
      type: "bar",
      orientation: "h",
      y: top.map(([iso]) => nombrePais(iso)),
      x: top.map(([, v]) => v[ind]),
      marker: { color: css("--ue"), cornerradius: 4 },
      text: top.map(([, v]) => fmtPct((v[ind] / totalUE) * 100)),
      textposition: "outside",
      textfont: { color: css("--text-secondary"), size: 12 },
      cliponaxis: false,
      customdata: top.map(([, v]) => fmtValor(v[ind], ind)),
      hovertemplate: "<b>%{y}</b><br>%{customdata}<br>%{text} de la UE<extra></extra>",
    };
    Plotly.react("g-top", [traza], layoutBase({
      margin: { l: 110, r: 48, t: 4, b: 32 },
      bargap: 0.35,
      xaxis: { showgrid: true, gridcolor: css("--grid"), zeroline: false, fixedrange: true, showticklabels: false },
      yaxis: { showgrid: false, fixedrange: true, automargin: true, color: css("--text-primary") },
    }), CONFIG);
    $("s-top").textContent = `Top 10 por ${nombreIndicador(ind)} · % sobre el total enviado a la UE-27 (${ue.length} países)`;
  }

  // ---------- Serie por producto ----------
  function seriesPorProducto(fnValor) {
    const anios = aniosSerie();
    const per = estado.periodo;
    return D.productos.map((nombre, p) => {
      const ys = anios.map((a) => fnValor(totales(a, per, (q) => q === p)));
      const enfasis = estado.producto === -1 || estado.producto === p;
      return { nombre, p, anios, ys, enfasis };
    });
  }

  function marcasEUDR() {
    const formas = [];
    const anotaciones = [];
    const marcas = [[2023, "EUDR en vigor"], [estado.anio, ""]];
    for (const [anio, texto] of marcas) {
      if (anio < estado.desde || anio > estado.hasta) continue;
      formas.push({ type: "line", xref: "x", yref: "paper", x0: anio, x1: anio, y0: 0, y1: 1, line: { color: texto ? css("--axis") : css("--text-muted"), width: 1 } });
      if (texto) anotaciones.push({ x: anio, y: 1, xref: "x", yref: "paper", text: texto, showarrow: false, xanchor: "left", yanchor: "top", xshift: 4, font: { size: 11, color: css("--text-muted") } });
    }
    return { shapes: formas, annotations: anotaciones };
  }

  function trazasLinea(series, fmt) {
    return series.map((s) => ({
      type: "scatter",
      mode: "lines+markers",
      name: s.nombre,
      x: s.anios,
      y: s.ys,
      line: { color: colorProducto(s.p), width: s.enfasis ? 2.5 : 1.5 },
      marker: { size: 6, color: colorProducto(s.p) },
      opacity: s.enfasis ? 1 : 0.25,
      customdata: s.ys.map(fmt),
      hovertemplate: `${s.nombre}: %{customdata}<extra></extra>`,
    }));
  }

  function renderSerie() {
    const ind = estado.indicador;
    const series = seriesPorProducto((t) => t.ue[ind]);
    const yTicks = ind === "fob" ? { tickprefix: "$", ticksuffix: "M" } : { ticksuffix: " t" };
    const escala = ind === "fob" ? 1e6 : 1e3;
    const trazas = trazasLinea(series, (v) => fmtValor(v, ind)).map((tr) => Object.assign(tr, { y: tr.y.map((v) => v / escala) }));
    Plotly.react("g-serie", trazas, layoutBase(Object.assign({
      hovermode: "x unified",
      yaxis: Object.assign({ gridcolor: css("--grid"), zeroline: false, fixedrange: true, rangemode: "tozero", separatethousands: true }, yTicks),
      xaxis: { showgrid: false, linecolor: css("--axis"), fixedrange: true, dtick: 2 },
    }, marcasEUDR())), CONFIG);
    leyenda("l-serie", series.map((s) => ({ nombre: s.nombre, color: colorProducto(s.p), opacidad: s.enfasis ? 1 : 0.35 })));
    const per = estado.periodo === "parcial" ? `${textoPeriodo()} de cada año` : "años completos";
    $("t-serie").textContent = `${ind === "fob" ? "Valor FOB" : "Volumen"} exportado a la UE-27 por producto`;
    $("s-serie").textContent = `${ind === "fob" ? "Millones de US$" : "Toneladas"} · ${per} · ${estado.desde}–${Math.min(estado.hasta, aniosSerie().at(-1) ?? estado.hasta)}`;
  }

  function renderParticipacion() {
    const ind = estado.indicador;
    const series = seriesPorProducto((t) => (t.mundo[ind] > 0 ? (t.ue[ind] / t.mundo[ind]) * 100 : null));
    Plotly.react("g-part", trazasLinea(series, fmtPct), layoutBase(Object.assign({
      hovermode: "x unified",
      yaxis: { gridcolor: css("--grid"), zeroline: false, fixedrange: true, range: [0, 100], ticksuffix: " %" },
      xaxis: { showgrid: false, linecolor: css("--axis"), fixedrange: true, dtick: 2 },
    }, marcasEUDR())), CONFIG);
    leyenda("l-part", series.map((s) => ({ nombre: s.nombre, color: colorProducto(s.p), opacidad: s.enfasis ? 1 : 0.35 })));
    $("s-part").textContent = `Participación de la UE-27 en el total exportado de cada producto, según ${nombreIndicador(ind)}`;
  }

  // ---------- Composición ----------
  function renderComposicion() {
    const per = periodoEfectivo(estado.anio);
    const ind = estado.indicador;
    const iv = per === "parcial" ? (ind === "fob" ? 5 : 6) : (ind === "fob" ? 3 : 4);
    // filas sub: [anio, s, ue, fob, kg, fob_p, kg_p]; subgrupos: [p, nombre]
    const acum = new Map();
    for (const f of D.sub) {
      if (f[0] !== estado.anio) continue;
      const [p, nombre] = D.subgrupos[f[1]];
      if (!productoIncluido(p)) continue;
      const clave = estado.producto === -1 ? D.productos[p] : nombre;
      const o = acum.get(clave) || { ue: 0, resto: 0, p };
      o[f[2] === 1 ? "ue" : "resto"] += f[iv];
      acum.set(clave, o);
    }
    const totUE = [...acum.values()].reduce((s, o) => s + o.ue, 0);
    const totResto = [...acum.values()].reduce((s, o) => s + o.resto, 0);
    const cats = [...acum.entries()].filter(([, o]) => o.ue + o.resto > 0).sort((a, b) => (a[1].ue + a[1].resto) - (b[1].ue + b[1].resto));
    const y = cats.map(([c]) => c);
    const traza = (bloque, nombre, color, total) => ({
      type: "bar",
      orientation: "h",
      name: nombre,
      y,
      x: cats.map(([, o]) => (total > 0 ? (o[bloque] / total) * 100 : 0)),
      marker: { color, cornerradius: 3 },
      customdata: cats.map(([, o]) => fmtValor(o[bloque], ind)),
      hovertemplate: `<b>%{y}</b><br>${nombre}: %{x:.1f} %<br>%{customdata}<extra></extra>`,
    });
    Plotly.react("g-comp", [traza("resto", "Resto del mundo", css("--resto"), totResto), traza("ue", "UE-27", css("--ue"), totUE)], layoutBase({
      barmode: "group",
      bargap: 0.3,
      bargroupgap: 0.12,
      margin: { l: 10, r: 16, t: 4, b: 36 },
      xaxis: { gridcolor: css("--grid"), showgrid: true, zeroline: false, fixedrange: true, ticksuffix: " %", rangemode: "tozero" },
      yaxis: { showgrid: false, fixedrange: true, automargin: true, color: css("--text-primary") },
    }), CONFIG);
    leyenda("l-comp", [{ nombre: "UE-27", color: css("--ue") }, { nombre: "Resto del mundo", color: css("--resto") }]);
    $("s-comp").textContent = `% de lo enviado a cada bloque · ${nombreIndicador(ind)} · ${etiquetaPeriodo(estado.anio)}`;
  }

  // ---------- Valor unitario ----------
  function renderPrecio() {
    const anios = aniosSerie();
    const per = estado.periodo;
    let trazas, items;
    if (estado.producto === -1) {
      const series = D.productos.map((nombre, p) => ({
        nombre, p, anios, enfasis: true,
        ys: anios.map((a) => { const t = totales(a, per, (q) => q === p); return t.ue.kg > 0 ? t.ue.fob / t.ue.kg : null; }),
      }));
      trazas = trazasLinea(series, (v) => (v == null ? "—" : nf2.format(v) + " US$/kg"));
      items = series.map((s) => ({ nombre: s.nombre + " (UE)", color: colorProducto(s.p) }));
      $("s-precio").textContent = "US$ FOB por kg exportado a la UE-27, por producto";
    } else {
      const p = estado.producto;
      const vu = (b) => anios.map((a) => { const t = totales(a, per, (q) => q === p); return t[b].kg > 0 ? t[b].fob / t[b].kg : null; });
      const linea = (nombre, ys, color) => ({
        type: "scatter", mode: "lines+markers", name: nombre, x: anios, y: ys,
        line: { color, width: 2.5 }, marker: { size: 6, color },
        customdata: ys.map((v) => (v == null ? "—" : nf2.format(v))),
        hovertemplate: `${nombre}: %{customdata} US$/kg<extra></extra>`,
      });
      trazas = [linea("UE-27", vu("ue"), css("--ue")), linea("Resto del mundo", vu("resto"), css("--resto"))];
      items = [{ nombre: "UE-27", color: css("--ue") }, { nombre: "Resto del mundo", color: css("--resto") }];
      $("s-precio").textContent = `${D.productos[p]}: US$ FOB por kg, UE-27 frente al resto del mundo`;
    }
    Plotly.react("g-precio", trazas, layoutBase(Object.assign({
      hovermode: "x unified",
      yaxis: { gridcolor: css("--grid"), zeroline: false, fixedrange: true, rangemode: "tozero", tickprefix: "$" },
      xaxis: { showgrid: false, linecolor: css("--axis"), fixedrange: true, dtick: 2 },
    }, marcasEUDR())), CONFIG);
    leyenda("l-precio", items);
  }

  // ---------- Tabla ----------
  function renderTabla() {
    const per = periodoEfectivo(estado.anio);
    const datos = [...porPais(estado.anio, per)].filter(([, v]) => v.fob > 0 || v.kg > 0);
    const totalFob = datos.reduce((s, [, v]) => s + v.fob, 0);
    filasTabla = datos.map(([iso, v]) => ({
      iso, nombre: nombrePais(iso), ue: esUE(iso), fob: v.fob, kg: v.kg,
      vu: v.kg > 0 ? v.fob / v.kg : NaN, part: (v.fob / totalFob) * 100,
    }));
    dibujarTabla();
    const prod = estado.producto === -1 ? "Café, cacao y madera" : D.productos[estado.producto];
    $("t-tabla").textContent = `Tabla por país de destino · ${prod} · ${etiquetaPeriodo(estado.anio)}`;
    $("s-tabla").textContent = `${filasTabla.length} destinos · ${filasTabla.filter((f) => f.ue).length} de la UE-27 (marcados con «UE»). % del total según valor FOB.`;
  }
  function dibujarTabla() {
    const { col, desc } = ordenTabla;
    filasTabla.sort((a, b) => {
      const va = a[col], vb = b[col];
      const r = typeof va === "string" ? va.localeCompare(vb, "es") : (isNaN(va) ? -Infinity : va) - (isNaN(vb) ? -Infinity : vb);
      return desc ? -r : r;
    });
    document.querySelector("#tabla tbody").innerHTML = filasTabla
      .map((f) => `<tr class="${f.ue ? "es-ue" : ""}"><td>${f.nombre}</td><td>${nf0.format(f.fob)}</td><td>${nf1.format(f.kg / 1000)}</td><td>${isNaN(f.vu) ? "—" : nf2.format(f.vu)}</td><td>${nf1.format(f.part)}</td></tr>`)
      .join("");
    for (const th of document.querySelectorAll("#tabla th")) {
      th.setAttribute("aria-sort", th.dataset.col === col ? (desc ? "descending" : "ascending") : "none");
    }
  }
  function descargarCSV() {
    const prod = estado.producto === -1 ? "cafe-cacao-madera" : D.productos[estado.producto].normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
    const cab = "pais,iso3,es_ue,fob_usd,peso_neto_kg,usd_por_kg,participacion_fob_pct";
    const filas = filasTabla.map((f) => [`"${f.nombre}"`, f.iso, f.ue ? 1 : 0, f.fob.toFixed(2), f.kg.toFixed(1), isNaN(f.vu) ? "" : f.vu.toFixed(3), f.part.toFixed(2)].join(","));
    const blob = new Blob(["﻿" + [cab, ...filas].join("\n")], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `exportaciones_${prod}_${estado.anio}_${periodoEfectivo(estado.anio)}.csv`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  // ---------- Hallazgos ----------
  function renderHallazgos() {
    $("hallazgos").innerHTML = HALLAZGOS.map((h, i) => `
      <article class="tarjeta hallazgo">
        <div class="numero">HALLAZGO ${i + 1}</div>
        <h3>${h.titulo}</h3>
        <p>${h.texto}</p>
      </article>`).join("");
  }

  // ---------- Render general ----------
  function render() {
    actualizarAvisoPeriodo();
    renderKPIs();
    renderMapa();
    renderTop();
    renderSerie();
    renderParticipacion();
    renderComposicion();
    renderPrecio();
    renderTabla();
  }

  // ---------- Tema ----------
  function aplicarTemaGuardado() {
    try {
      const t = localStorage.getItem("tema-eudr");
      if (t === "light" || t === "dark") document.documentElement.dataset.theme = t;
    } catch (e) { /* almacenamiento no disponible */ }
  }
  function alternarTema() {
    const oscuroActual = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === "dark"
      : window.matchMedia("(prefers-color-scheme: dark)").matches;
    const nuevo = oscuroActual ? "light" : "dark";
    document.documentElement.dataset.theme = nuevo;
    try { localStorage.setItem("tema-eudr", nuevo); } catch (e) { /* sin almacenamiento */ }
    construirControles();
    render();
  }

  // ---------- Inicio ----------
  async function iniciar() {
    aplicarTemaGuardado();
    if (typeof Plotly === "undefined") {
      $("cargando").textContent = "No se pudo cargar la librería de gráficos (Plotly). Revisa tu conexión y recarga la página.";
      return;
    }
    try {
      const [r1, r2] = await Promise.all([fetch("data/datos.json"), fetch("data/hallazgos.json")]);
      D = await r1.json();
      HALLAZGOS = r2.ok ? await r2.json() : [];
    } catch (e) {
      $("cargando").textContent = "No se pudieron cargar los datos. Si abriste el archivo directamente, sírvelo con un servidor (por ejemplo: python -m http.server).";
      return;
    }
    indexar();
    estado.anio = D.meta.anio_parcial - 1;
    estado.hasta = D.meta.anio_parcial - 1;
    estado.desde = Math.max(D.meta.anio_min, 2012);
    $("cargando").remove();
    $("chip-cobertura").textContent = `Cobertura: ${D.meta.anio_min} – ${MESES[D.meta.ultimo_mes - 1]} ${D.meta.anio_max}`;
    $("pie-actualizado").textContent = ` Datos descargados el ${D.meta.actualizado}.`;
    construirControles();
    renderHallazgos();
    render();

    for (const th of document.querySelectorAll("#tabla th")) {
      th.addEventListener("click", () => {
        const col = th.dataset.col;
        ordenTabla = { col, desc: ordenTabla.col === col ? !ordenTabla.desc : col !== "nombre" };
        dibujarTabla();
      });
    }
    $("descargar").addEventListener("click", descargarCSV);
    $("boton-tema").addEventListener("click", alternarTema);
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { if (!document.documentElement.dataset.theme) { construirControles(); render(); } });
  }

  iniciar();
})();
