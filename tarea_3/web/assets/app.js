/* Dashboard: precios internacionales y exportaciones peruanas de café y cacao, 2015-2025.
   Lee data/datos.json (generado por 02_procesar_datos.ipynb) y data/hallazgos.json (03_analisis.ipynb). */
(() => {
  "use strict";

  const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre"];
  // Regiones para los gráficos: las tres más pequeñas se juntan en "Otros"
  const GRUPOS = ["Unión Europea", "Resto de Europa", "Norteamérica", "América Latina y el Caribe", "Asia y Medio Oriente", "Otros (África, Oceanía, sin país)"];
  const KG_MINIMO_MES = 100000; // meses con menos de 100 t del producto base: su valor unitario no es representativo
  // Formato del sistema internacional, como en los notebooks: espacio fino para miles y coma decimal (1 802,5)
  const formato = (dec) => {
    const f = new Intl.NumberFormat("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec });
    return { format: (v) => f.format(v).replace(/,/g, " ").replace(".", ",") };
  };
  const nf0 = formato(0);
  const nf1 = formato(1);
  const nf2 = formato(2);

  let D = null;          // datos
  let TEXTOS = { hallazgos: [], propuestas: [] };
  const estado = { producto: 0, anio: null, indicador: "fob" };
  let ordenTabla = { col: "fob", desc: true };
  let filasTabla = [];

  // ---------- utilidades ----------
  const $ = (id) => document.getElementById(id);
  const css = (nombre) => getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
  const grupoDe = (region) => Math.min(region, GRUPOS.length - 1);
  const colorGrupo = (g) => css(`--r-${g}`);
  const rango = (a, b) => Array.from({ length: b - a + 1 }, (_, i) => a + i);

  function fmtUSD(v) {
    const m = v / 1e6;
    return "US$ " + (Math.abs(m) >= 100 ? nf0.format(m) : nf1.format(m)) + " M";
  }
  const fmtConSigno = (v) => (v >= 0 ? "+" : "−") + fmtUSD(Math.abs(v));
  function fmtPeso(kg) {
    const t = kg / 1000;
    if (Math.abs(t) >= 10000) return nf1.format(t / 1000) + " mil t";
    return nf0.format(t) + " t";
  }
  const fmtValor = (v, ind) => (ind === "fob" ? fmtUSD(v) : fmtPeso(v));
  // Versión para tarjetas KPI: la unidad va en tamaño menor
  const unidadPequena = (texto) => texto.replace(/US\$ /, "<small>US$</small> ").replace(/ (M|mil t|t)$/, " <small>$1</small>");
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
  const fmtPct = (v) => (v != null && isFinite(v) ? nf1.format(v) + " %" : "—");
  const nombreIndicador = (ind) => (ind === "fob" ? "valor FOB" : "volumen (peso neto)");

  function deltaPct(v) {
    if (v == null || !isFinite(v)) return "";
    return `<span class="${v >= 0 ? "delta-sube" : "delta-baja"}">${v >= 0 ? "▲ +" : "▼ −"}${nf1.format(Math.abs(v))} %</span>`;
  }
  function deltaPP(actual, previo) {
    if (actual == null || previo == null) return "";
    const d = actual - previo;
    return `<span class="${d >= 0 ? "delta-sube" : "delta-baja"}">${d >= 0 ? "▲ +" : "▼ −"}${nf1.format(Math.abs(d))} p.p.</span>`;
  }

  const esParcial = (anio) => anio === D.meta.anio_parcial;
  const periodo = (anio) => (esParcial(anio) ? "ene_ago" : "anual");
  const textoPeriodo = () => `enero–${MESES[D.meta.ultimo_mes - 1]}`;
  const etiqueta = (anio) => (esParcial(anio) ? `${anio} (ene–${MESES[D.meta.ultimo_mes - 1].slice(0, 3)})` : String(anio));
  // Año anterior con los mismos meses, para que 2026 nunca se lea como año completo
  const anioPrevio = (anio) => (esParcial(anio) ? `${anio - 1} (ene–${MESES[D.meta.ultimo_mes - 1].slice(0, 3)})` : String(anio - 1));
  // Eje categórico: «2026 (ene–ago)» se parte en dos líneas
  const ticks = (x) => ({ tickvals: x, ticktext: x.map((s) => s.replace(" (", "<br>(")) });
  const nombrePais = (iso) => (D.paises[iso] ? D.paises[iso][0] : iso);
  const regionPais = (iso) => (D.paises[iso] ? D.paises[iso][1] : D.regiones.length - 1);
  const anios = () => rango(D.meta.anio_inicio, D.meta.anio_fin);

  // índices
  let IND = new Map();
  let porAnio = new Map();
  const ind = (per, p, anio) => IND.get(`${per}|${p}|${anio}`);
  function indexar() {
    IND = new Map(D.ind.map((r) => [`${r.periodo}|${r.p}|${r.anio}`, r]));
    porAnio = new Map();
    for (const f of D.pais) {
      if (!porAnio.has(f[0])) porAnio.set(f[0], []);
      porAnio.get(f[0]).push(f);
    }
  }

  // Agrega por país para un año: Map iso -> {fob, kg}. Fila: [anio, p, iso3, fob, kg, fob_p, kg_p]
  function porPais(anio, per, p) {
    const m = new Map();
    for (const f of porAnio.get(anio) || []) {
      if (f[1] !== p) continue;
      const o = m.get(f[2]) || { fob: 0, kg: 0 };
      o.fob += per === "ene_ago" ? f[5] : f[3];
      o.kg += per === "ene_ago" ? f[6] : f[4];
      m.set(f[2], o);
    }
    return m;
  }

  // ---------- Plotly: estilo común ----------
  function layoutBase(extra = {}) {
    const base = {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      separators: ", ",

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
      .map((it) => `<span>${it.raya ? '<i class="raya"></i>' : `<i class="punto" style="background:${it.color}"></i>`}${it.nombre}</span>`)
      .join("");
  }
  // Etiqueta directa al final de una línea (texto en tinta, no en el color de la serie)
  const etiquetaFinal = (x, y, texto) => ({
    x, y, text: texto, showarrow: false, xanchor: "left", xshift: 8, font: { size: 12, color: css("--text-secondary") },
  });

  // ---------- Controles ----------
  function segmentado(idContenedor, opciones, clave) {
    const cont = $(idContenedor);
    cont.innerHTML = "";
    for (const op of opciones) {
      const b = document.createElement("button");
      b.type = "button";
      b.dataset.valor = String(op.valor);
      b.textContent = op.texto;
      b.addEventListener("click", () => {
        estado[clave] = op.valor;
        marcar(idContenedor, clave);
        render();
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
    segmentado("f-producto", D.productos.map((n, i) => ({ valor: i, texto: n })), "producto");
    segmentado("f-indicador", [{ valor: "fob", texto: "Valor FOB" }, { valor: "kg", texto: "Volumen" }], "indicador");
    const lista = rango(D.meta.anio_inicio, D.meta.anio_parcial).reverse();
    $("f-anio").innerHTML = lista.map((a) => `<option value="${a}">${etiqueta(a)}</option>`).join("");
    $("f-anio").value = String(estado.anio);
    $("f-anio").onchange = (e) => {
      estado.anio = Number(e.target.value);
      render();
    };
  }

  function actualizarAviso() {
    $("aviso-periodo").textContent = esParcial(estado.anio)
      ? `${estado.anio} tiene datos hasta ${MESES[D.meta.ultimo_mes - 1]}: se compara ${textoPeriodo()} de ${estado.anio} con el mismo periodo de ${estado.anio - 1}.`
      : `Años completos. ${D.meta.anio_parcial} (${textoPeriodo()}) está disponible en el selector de año.`;
  }

  // ---------- KPIs ----------
  function renderKPIs() {
    const p = estado.producto;
    const a = estado.anio;
    const per = periodo(a);
    const x = ind(per, p, a);
    const prev = ind(per, p, a - 1);
    const etq = etiqueta(a);
    const cambio = x.efecto_precio + x.efecto_volumen;
    // Parte del cambio total: solo tiene sentido si el efecto va en la misma dirección que el cambio y no lo supera
    const parte = (efecto) => (cambio !== 0 && Math.sign(efecto) === Math.sign(cambio) && Math.abs(efecto) <= Math.abs(cambio)
      ? ` · ${nf0.format((efecto / cambio) * 100)} % del total` : "");
    const tarjetas = [
      { titulo: `Valor exportado · ${etq}`, valor: unidadPequena(fmtUSD(x.fob)), detalle: `${deltaPct(x.var_fob)} vs ${anioPrevio(a)}` },
      { titulo: `Volumen · ${etq}`, valor: unidadPequena(fmtPeso(x.kg)), detalle: `${deltaPct(x.var_kg)} vs ${anioPrevio(a)}` },
      { titulo: `Valor unitario del ${D.base[p].toLowerCase()}`, valor: `${nf2.format(x.vu_base)} <small>US$/kg</small>`, detalle: `${deltaPct(x.var_vu_base)} · FOB en puerto peruano` },
      { titulo: `Precio internacional · ${D.precio_ref[p].split(" (")[0].toLowerCase()}`, valor: `${nf2.format(x.precio_int)} <small>US$/kg</small>`, detalle: `${deltaPct(x.var_precio_int)} · promedio ${per === "ene_ago" ? textoPeriodo() : "del año"}` },
      { titulo: `Cambio del valor por precio`, valor: unidadPequena(fmtConSigno(x.efecto_precio)), detalle: `de un cambio total de ${fmtConSigno(cambio)} vs ${anioPrevio(a)}${parte(x.efecto_precio)}` },
      { titulo: `Cambio del valor por volumen`, valor: unidadPequena(fmtConSigno(x.efecto_volumen)), detalle: `de un cambio total de ${fmtConSigno(cambio)} vs ${anioPrevio(a)}${parte(x.efecto_volumen)}` },
      { titulo: "Mercados equivalentes", valor: nf1.format(x.mercados_equivalentes), detalle: `${nf0.format(x.n_destinos)} destinos · 1.º ${nombrePais(x.principal)} (${fmtPct(x.principal_part)})` },
      { titulo: "Parte de la Unión Europea", valor: fmtPct(x.part_ue), detalle: `${deltaPP(x.part_ue, prev ? prev.part_ue : null)} vs ${anioPrevio(a)}` },
    ];
    $("kpis").innerHTML = tarjetas
      .map((k) => `<div class="kpi"><div class="titulo">${k.titulo}</div><div class="valor">${k.valor}</div><div class="detalle">${k.detalle}</div></div>`)
      .join("");
  }

  // ---------- Precio internacional vs valor unitario (mensual) ----------
  function renderPrecio() {
    const p = estado.producto;
    const filas = D.mensual.filter((f) => f[1] === p);
    const x = filas.map((f) => `${f[0]}-15`);
    const precio = filas.map((f) => f[4]);
    const vu = filas.map((f) => (f[3] != null && f[3] >= KG_MINIMO_MES ? f[2] : null));
    const ref = D.precio_ref[p];
    const nombreVU = `Valor unitario FOB del ${D.base[p].toLowerCase()} peruano`;
    const a = estado.anio;
    const fin = esParcial(a) ? `${a}-${String(D.meta.ultimo_mes + 1).padStart(2, "0")}-01` : `${a + 1}-01-01`;
    const trazas = [
      {
        type: "scatter", mode: "lines", x, y: precio, name: ref,
        line: { color: css("--referencia"), width: 2, dash: "dash" },
        hovertemplate: `Precio internacional: %{y:.2f} US$/kg<extra></extra>`,
      },
      {
        type: "scatter", mode: "lines", x, y: vu, name: nombreVU, connectgaps: false,
        line: { color: css("--m-precio"), width: 2 },
        hovertemplate: `Valor unitario Perú: %{y:.2f} US$/kg<extra></extra>`,
      },
    ];
    Plotly.react("g-precio", trazas, layoutBase({
      hovermode: "x unified",
      xaxis: { type: "date", showgrid: false, linecolor: css("--axis"), fixedrange: true, dtick: "M12", tickformat: "%Y", hoverformat: "%m/%Y" },
      yaxis: { gridcolor: css("--grid"), zeroline: false, fixedrange: true, rangemode: "tozero", tickprefix: "$" },
      shapes: [{ type: "rect", xref: "x", yref: "paper", x0: `${a}-01-01`, x1: fin, y0: 0, y1: 1, fillcolor: css("--grid"), opacity: 0.6, line: { width: 0 }, layer: "below" }],
    }), CONFIG);
    leyenda("l-precio", [{ nombre: `Precio internacional: ${ref}`, raya: true }, { nombre: nombreVU, color: css("--m-precio") }]);
    $("t-precio").textContent = `${D.productos[p]}: precio internacional y valor unitario de exportación`;
    $("s-precio").textContent = `US$/kg, mensual, enero ${D.meta.anio_inicio} – ${MESES[Number(D.meta.ultimo_mes_precio.slice(5)) - 1]} ${D.meta.ultimo_mes_precio.slice(0, 4)}. Franja: ${etiqueta(a)}. Se omiten los meses con menos de 100 t exportadas.`;
  }

  // ---------- Descomposición precio / volumen ----------
  function renderDescomposicion() {
    const p = estado.producto;
    const filas = anios().map((a) => ind("anual", p, a)).concat([ind("ene_ago", p, D.meta.anio_parcial)]);
    const x = anios().map(String).concat([etiqueta(D.meta.anio_parcial)]);
    const ep = filas.map((f) => f.efecto_precio / 1e6);
    const ev = filas.map((f) => f.efecto_volumen / 1e6);
    const tot = filas.map((f) => (f.efecto_precio + f.efecto_volumen) / 1e6);
    const hover = (nombre) => `<b>%{x}</b><br>${nombre}: %{customdata}<extra></extra>`;
    const barra = (ys, nombre, color) => ({
      type: "bar", x, y: ys, name: nombre, marker: { color, cornerradius: 3, line: { color: css("--surface-1"), width: 1 } },
      customdata: ys.map((v) => fmtConSigno(v * 1e6)), hovertemplate: hover(nombre),
    });
    const i = x.indexOf(etiqueta(estado.anio));
    Plotly.react("g-desc", [
      barra(ep, "Efecto precio", css("--m-precio")),
      barra(ev, "Efecto volumen", css("--m-volumen")),
      {
        type: "scatter", mode: "markers", x, y: tot, name: "Cambio total",
        marker: { symbol: "diamond", size: 9, color: css("--text-primary"), line: { color: css("--surface-1"), width: 1.5 } },
        customdata: tot.map((v) => fmtConSigno(v * 1e6)), hovertemplate: hover("Cambio total"),
      },
    ], layoutBase({
      barmode: "relative",
      bargap: 0.3,
      hovermode: "closest",
      yaxis: { gridcolor: css("--grid"), zeroline: true, zerolinecolor: css("--axis"), fixedrange: true, tickprefix: "$", ticksuffix: " M", separatethousands: true },
      xaxis: { showgrid: false, linecolor: css("--axis"), fixedrange: true, type: "category", tickangle: 0, ...ticks(x) },
      shapes: i >= 0 ? [{ type: "rect", xref: "x", yref: "paper", x0: i - 0.5, x1: i + 0.5, y0: 0, y1: 1, fillcolor: css("--grid"), opacity: 0.6, line: { width: 0 }, layer: "below" }] : [],
    }), CONFIG);
    leyenda("l-desc", [
      { nombre: "Efecto precio", color: css("--m-precio") },
      { nombre: "Efecto volumen", color: css("--m-volumen") },
      { nombre: "Cambio total (◆)", color: css("--text-primary") },
    ]);
    $("t-desc").textContent = `¿Precio o volumen? ${D.productos[p]}: cambio anual del valor exportado`;
    $("s-desc").textContent = "Millones de US$ FOB respecto al año anterior. Las barras suman el cambio total.";
    $("n-desc").textContent = `${etiqueta(D.meta.anio_parcial)}: ${textoPeriodo()} de ${D.meta.anio_parcial} frente a ${textoPeriodo()} de ${D.meta.anio_parcial - 1}.`;
  }

  // ---------- Índices valor, volumen y valor unitario ----------
  function renderIndice() {
    const p = estado.producto;
    const lista = anios();
    const filas = lista.map((a) => ind("anual", p, a));
    const b = filas[0];
    const series = [
      { nombre: "Valor FOB", color: css("--m-valor"), ys: filas.map((f) => (f.fob / b.fob) * 100) },
      { nombre: "Volumen", color: css("--m-volumen"), ys: filas.map((f) => (f.kg / b.kg) * 100) },
      { nombre: "Valor unitario", color: css("--m-precio"), ys: filas.map((f) => (f.vu / b.vu) * 100) },
    ];
    const ultimo = lista[lista.length - 1];
    Plotly.react("g-indice", series.map((s) => ({
      type: "scatter", mode: "lines+markers", x: lista, y: s.ys, name: s.nombre,
      line: { color: s.color, width: 2 }, marker: { size: 6, color: s.color },
      hovertemplate: `${s.nombre}: %{y:.0f}<extra></extra>`,
    })), layoutBase({
      hovermode: "x unified",
      margin: { l: 48, r: 112, t: 8, b: 36 },
      yaxis: { gridcolor: css("--grid"), zeroline: false, fixedrange: true, rangemode: "tozero" },
      xaxis: { showgrid: false, linecolor: css("--axis"), fixedrange: true, dtick: 2, range: [lista[0] - 0.4, ultimo + 0.4] },
      shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: 100, y1: 100, line: { color: css("--axis"), width: 1, dash: "dot" } }],
      annotations: series.map((s) => etiquetaFinal(ultimo, s.ys[s.ys.length - 1], `${s.nombre}: ${nf0.format(s.ys[s.ys.length - 1])}`)),
    }), CONFIG);
    leyenda("l-indice", series.map((s) => ({ nombre: s.nombre, color: s.color })));
    $("t-indice").textContent = `${D.productos[p]}: valor, volumen y valor unitario`;
    $("s-indice").textContent = `Índice ${D.meta.anio_inicio} = 100, años completos. Valor = volumen × valor unitario.`;
  }

  // ---------- Mapa ----------
  let colaMapa = Promise.resolve();
  function renderMapa() {
    const p = estado.producto;
    const per = periodo(estado.anio);
    const indicador = estado.indicador;
    const datos = [...porPais(estado.anio, per, p)].filter(([iso, v]) => v[indicador] > 0 && !iso.startsWith("X"));
    const total = datos.reduce((s, [, v]) => s + v[indicador], 0);
    const z = datos.map(([, v]) => Math.log10(v[indicador]));
    const zmin = Math.floor(Math.min(...z, 5));
    const zmax = Math.ceil(Math.max(...z, zmin + 1));
    const ticks = rango(zmin, zmax);
    const traza = {
      type: "choropleth",
      locationmode: "ISO-3",
      locations: datos.map(([iso]) => iso),
      z, zmin, zmax,
      text: datos.map(([iso, v]) => `<b>${nombrePais(iso)}</b> · ${D.regiones[regionPais(iso)]}<br>${fmtValor(v[indicador], indicador)}<br>${fmtPct((v[indicador] / total) * 100)} del total`),
      hovertemplate: "%{text}<extra></extra>",
      colorscale: [[0, css("--seq-100")], [0.33, css("--seq-250")], [0.6, css("--seq-400")], [0.8, css("--seq-550")], [1, css("--seq-700")]],
      marker: { line: { color: css("--surface-1"), width: 0.6 } },
      colorbar: { thickness: 10, len: 0.7, outlinewidth: 0, tickvals: ticks, ticktext: ticks.map((k) => fmtCorto(10 ** k, indicador)), tickfont: { color: css("--text-secondary"), size: 11 } },
    };
    const geo = {
      scope: "world", projection: { type: "natural earth" }, showframe: false, showcoastlines: false,
      showland: true, landcolor: css("--surface-2"), showcountries: true, countrycolor: css("--grid"), showocean: false,
      bgcolor: "rgba(0,0,0,0)", lataxis: { range: [-58, 85] },
    };
    // El mapa carga su topojson de forma asíncrona: se encolan los redibujos para que un clic rápido no pise al anterior
    const layout = layoutBase({ geo, margin: { l: 0, r: 0, t: 0, b: 0 }, dragmode: false });
    colaMapa = colaMapa.then(() => Plotly.react("g-mapa", [traza], layout, CONFIG)).catch((e) => console.warn("Mapa:", e));
    $("t-mapa").textContent = `${D.productos[p]}: países de destino, ${etiqueta(estado.anio)}`;
    $("s-mapa").textContent = `Color según ${nombreIndicador(indicador)} (escala logarítmica), ${datos.length} países. Pasa el cursor para ver el detalle.`;
  }

  // ---------- Top destinos ----------
  function renderTop() {
    const p = estado.producto;
    const indicador = estado.indicador;
    const todos = [...porPais(estado.anio, periodo(estado.anio), p)]
      .filter(([iso, v]) => v[indicador] > 0 && !iso.startsWith("X"))
      .sort((a, b) => b[1][indicador] - a[1][indicador]);
    const total = todos.reduce((s, [, v]) => s + v[indicador], 0);
    const top = todos.slice(0, 10).reverse();
    Plotly.react("g-top", [{
      type: "bar", orientation: "h",
      y: top.map(([iso]) => nombrePais(iso)),
      x: top.map(([, v]) => v[indicador]),
      marker: { color: top.map(([iso]) => colorGrupo(grupoDe(regionPais(iso)))), cornerradius: 4 },
      text: top.map(([, v]) => fmtPct((v[indicador] / total) * 100)),
      textposition: "outside", cliponaxis: false,
      textfont: { color: css("--text-secondary"), size: 12 },
      customdata: top.map(([iso, v]) => [fmtValor(v[indicador], indicador), D.regiones[regionPais(iso)]]),
      hovertemplate: "<b>%{y}</b> · %{customdata[1]}<br>%{customdata[0]}<br>%{text} del total<extra></extra>",
    }], layoutBase({
      margin: { l: 110, r: 52, t: 4, b: 24 },
      bargap: 0.35,
      xaxis: { showgrid: true, gridcolor: css("--grid"), zeroline: false, fixedrange: true, showticklabels: false },
      yaxis: { showgrid: false, fixedrange: true, automargin: true, color: css("--text-primary") },
    }), CONFIG);
    const presentes = [...new Set(top.map(([iso]) => grupoDe(regionPais(iso))))].sort();
    leyenda("l-top", presentes.map((g) => ({ nombre: GRUPOS[g], color: colorGrupo(g) })));
    $("t-top").textContent = `Principales destinos · ${etiqueta(estado.anio)}`;
    $("s-top").textContent = `Top 10 por ${nombreIndicador(indicador)}; % sobre el total (${todos.length} destinos). Color = región.`;
  }

  // ---------- Regiones ----------
  function renderRegion() {
    const p = estado.producto;
    const col = estado.indicador === "fob" ? 4 : 5;
    const lista = anios().map((a) => [a, "anual"]).concat([[D.meta.anio_parcial, "ene_ago"]]);
    const x = lista.map(([a]) => etiqueta(a));
    const acum = lista.map(() => new Array(GRUPOS.length).fill(0));
    lista.forEach(([a, per], i) => {
      for (const f of D.region) if (f[0] === per && f[1] === p && f[2] === a) acum[i][grupoDe(f[3])] += f[col];
    });
    const totales = acum.map((v) => v.reduce((s, y) => s + y, 0));
    const trazas = GRUPOS.map((nombre, g) => ({
      type: "bar", name: nombre, x,
      y: acum.map((v, i) => (totales[i] > 0 ? (v[g] / totales[i]) * 100 : 0)),
      marker: { color: colorGrupo(g), line: { color: css("--surface-1"), width: 1 } },
      customdata: acum.map((v) => fmtValor(v[g], estado.indicador)),
      hovertemplate: `<b>%{x}</b> · ${nombre}<br>%{y:.1f} % · %{customdata}<extra></extra>`,
    }));
    Plotly.react("g-region", trazas, layoutBase({
      barmode: "stack", bargap: 0.25, hovermode: "closest",
      yaxis: { gridcolor: css("--grid"), zeroline: false, fixedrange: true, range: [0, 100], ticksuffix: " %" },
      xaxis: { showgrid: false, linecolor: css("--axis"), fixedrange: true, type: "category", tickangle: 0, ...ticks(x) },
    }), CONFIG);
    leyenda("l-region", GRUPOS.map((nombre, g) => ({ nombre, color: colorGrupo(g) })));
    $("t-region").textContent = `${D.productos[p]}: ¿a qué regiones se vende?`;
    $("s-region").textContent = `% del ${nombreIndicador(estado.indicador)} por región de destino. ${D.meta.anio_parcial}: solo ${textoPeriodo()}.`;
  }

  // ---------- Diversificación ----------
  function renderDiversificacion() {
    const lista = anios();
    const ultimo = lista[lista.length - 1];
    const series = D.productos.map((nombre, p) => ({
      nombre, p, ys: lista.map((a) => ind("anual", p, a).mercados_equivalentes), enfasis: p === estado.producto,
    })).sort((a, b) => a.enfasis - b.enfasis);  // el producto elegido se dibuja encima
    const color = (s) => (s.enfasis ? css("--text-primary") : css("--referencia"));
    const formas = [];
    if (!esParcial(estado.anio)) {
      formas.push({ type: "line", xref: "x", yref: "paper", x0: estado.anio, x1: estado.anio, y0: 0, y1: 1, line: { color: css("--axis"), width: 1 } });
    }
    Plotly.react("g-divers", series.map((s) => ({
      type: "scatter", mode: "lines+markers", x: lista, y: s.ys, name: s.nombre,
      line: { color: color(s), width: s.enfasis ? 2.5 : 1.5 }, marker: { size: s.enfasis ? 7 : 5, color: color(s) },
      hovertemplate: `${s.nombre}: %{y:.1f} mercados equivalentes<extra></extra>`,
    })), layoutBase({
      hovermode: "x unified",
      margin: { l: 40, r: 64, t: 8, b: 36 },
      yaxis: { gridcolor: css("--grid"), zeroline: false, fixedrange: true, rangemode: "tozero" },
      xaxis: { showgrid: false, linecolor: css("--axis"), fixedrange: true, dtick: 2, range: [lista[0] - 0.4, ultimo + 0.4] },
      shapes: formas,
      annotations: series.map((s) => etiquetaFinal(ultimo, s.ys[s.ys.length - 1], s.nombre)),
    }), CONFIG);
    leyenda("l-divers", series.slice().reverse().map((s) => ({ nombre: s.nombre + (s.enfasis ? " (elegido)" : ""), color: color(s) })));
    $("s-divers").textContent = "Mercados equivalentes = 10 000 / índice Herfindahl por país (valor FOB). Más alto = ventas repartidas entre más países.";
  }

  // ---------- Tabla ----------
  function renderTabla() {
    const p = estado.producto;
    const per = periodo(estado.anio);
    const actual = porPais(estado.anio, per, p);
    const previo = porPais(estado.anio - 1, per, p);
    const datos = [...actual].filter(([, v]) => v.fob > 0 || v.kg > 0);
    const totalFob = datos.reduce((s, [, v]) => s + v.fob, 0);
    filasTabla = datos.map(([iso, v]) => {
      const ant = previo.get(iso);
      return {
        iso, nombre: nombrePais(iso), region: D.regiones[regionPais(iso)], fob: v.fob, kg: v.kg,
        vu: v.kg > 0 ? v.fob / v.kg : NaN, part: (v.fob / totalFob) * 100,
        var: ant && ant.fob > 0 ? (v.fob / ant.fob - 1) * 100 : NaN,
      };
    });
    dibujarTabla();
    $("t-tabla").textContent = `Tabla por país de destino · ${D.productos[p]} · ${etiqueta(estado.anio)}`;
    $("s-tabla").textContent = `${filasTabla.length} destinos. % del total según valor FOB; variación frente a ${anioPrevio(estado.anio)}.`;
  }
  function dibujarTabla() {
    const { col, desc } = ordenTabla;
    filasTabla.sort((a, b) => {
      const va = a[col], vb = b[col];
      const r = typeof va === "string" ? va.localeCompare(vb, "es") : (isNaN(va) ? -Infinity : va) - (isNaN(vb) ? -Infinity : vb);
      return desc ? -r : r;
    });
    const variacion = (v) => (isNaN(v) ? "nuevo" : `<span class="${v >= 0 ? "delta-sube" : "delta-baja"}">${v >= 0 ? "+" : "−"}${nf1.format(Math.abs(v))}</span>`);
    document.querySelector("#tabla tbody").innerHTML = filasTabla
      .map((f) => `<tr><td>${f.nombre}</td><td>${f.region}</td><td>${nf0.format(f.fob)}</td><td>${nf1.format(f.kg / 1000)}</td><td>${isNaN(f.vu) ? "—" : nf2.format(f.vu)}</td><td>${nf1.format(f.part)}</td><td>${variacion(f.var)}</td></tr>`)
      .join("");
    for (const th of document.querySelectorAll("#tabla th")) {
      th.setAttribute("aria-sort", th.dataset.col === col ? (desc ? "descending" : "ascending") : "none");
    }
  }
  function descargarCSV() {
    const prod = D.productos[estado.producto].normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
    const cab = "pais,iso3,region,fob_usd,peso_neto_kg,usd_por_kg,participacion_fob_pct,variacion_fob_pct";
    const filas = filasTabla.map((f) => [`"${f.nombre}"`, f.iso, `"${f.region}"`, f.fob.toFixed(2), f.kg.toFixed(1), isNaN(f.vu) ? "" : f.vu.toFixed(3), f.part.toFixed(2), isNaN(f.var) ? "" : f.var.toFixed(1)].join(","));
    const blob = new Blob(["﻿" + [cab, ...filas].join("\n")], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `exportaciones_${prod}_${estado.anio}_${periodo(estado.anio)}.csv`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  // ---------- Hallazgos y propuestas ----------
  function renderTextos() {
    $("hallazgos").innerHTML = TEXTOS.hallazgos.map((h, i) => `
      <article class="tarjeta hallazgo">
        <div class="numero">HALLAZGO ${i + 1}</div>
        <h3>${h.titulo}</h3>
        <p>${h.texto}</p>
      </article>`).join("");
    $("propuestas").innerHTML = TEXTOS.propuestas.map((h) => `
      <article class="tarjeta propuesta">
        <h3>${h.titulo}</h3>
        <p>${h.texto}</p>
      </article>`).join("");
  }

  // ---------- Render general ----------
  function render() {
    actualizarAviso();
    renderKPIs();
    renderPrecio();
    renderDescomposicion();
    renderIndice();
    renderMapa();
    renderTop();
    renderRegion();
    renderDiversificacion();
    renderTabla();
  }

  // ---------- Tema ----------
  function aplicarTemaGuardado() {
    try {
      const t = localStorage.getItem("tema-cafe-cacao");
      if (t === "light" || t === "dark") document.documentElement.dataset.theme = t;
    } catch (e) { /* almacenamiento no disponible */ }
  }
  function alternarTema() {
    const oscuroActual = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === "dark"
      : window.matchMedia("(prefers-color-scheme: dark)").matches;
    const nuevo = oscuroActual ? "light" : "dark";
    document.documentElement.dataset.theme = nuevo;
    try { localStorage.setItem("tema-cafe-cacao", nuevo); } catch (e) { /* sin almacenamiento */ }
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
      if (r2.ok) TEXTOS = await r2.json();
    } catch (e) {
      $("cargando").textContent = "No se pudieron cargar los datos. Si abriste el archivo directamente, sírvelo con un servidor (por ejemplo: python -m http.server).";
      return;
    }
    indexar();
    estado.anio = D.meta.anio_fin;
    $("cargando").remove();
    $("chip-cobertura").textContent = `Cobertura: ${D.meta.anio_inicio} – ${MESES[D.meta.ultimo_mes - 1]} ${D.meta.anio_parcial}`;
    $("lim-parcial").textContent = `${D.meta.anio_parcial} solo tiene ${textoPeriodo()}: se compara con ${textoPeriodo()} de ${D.meta.anio_parcial - 1} y se rotula «${etiqueta(D.meta.anio_parcial)}».`;
    $("pie-actualizado").textContent = ` Exportaciones descargadas el ${D.meta.actualizado_sunat}; precios del Banco Mundial actualizados el ${D.meta.actualizado_precios}.`;
    construirControles();
    renderTextos();
    render();

    for (const th of document.querySelectorAll("#tabla th")) {
      th.addEventListener("click", () => {
        const col = th.dataset.col;
        ordenTabla = { col, desc: ordenTabla.col === col ? !ordenTabla.desc : !["nombre", "region"].includes(col) };
        dibujarTabla();
      });
    }
    $("descargar").addEventListener("click", descargarCSV);
    $("boton-tema").addEventListener("click", alternarTema);
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { if (!document.documentElement.dataset.theme) render(); });
  }

  iniciar();
})();
