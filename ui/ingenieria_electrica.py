def _mostrar_detalle_electrico_completo(paneles, electrical):

    st.markdown("## ⚡ Detalle eléctrico completo")

    if not paneles or not electrical:
        st.warning("Sin datos suficientes")
        return

    strings = getattr(paneles, "strings", [])
    panel = getattr(paneles, "panel", None)

    corr = getattr(electrical, "corrientes", None)
    conductores = getattr(electrical, "conductores", None)
    protecciones = getattr(electrical, "protecciones", None)

    # ======================================================
    # 🔹 PANEL
    # ======================================================
    if panel and corr:
        st.markdown("### 🔹 Nivel Panel")

        st.table({
            "Parámetro": ["Imp", "Isc", "Corriente diseño"],
            "Valor": [
                f"{panel.imp_a:.2f} A",
                f"{panel.isc_a:.2f} A",
                f"{corr.panel.i_diseno_a:.2f} A"
            ]
        })

    # ======================================================
    # 🔹 STRING
    # ======================================================
    if strings:
        st.markdown("### 🔗 Nivel String")

        data = []

        for i, s in enumerate(strings, start=1):
            data.append({
                "String": i,
                "Paneles": s.n_series,
                "Vmp": f"{s.vmp_string_v:.2f} V",
                "Voc": f"{s.voc_frio_string_v:.2f} V",
                "Corriente": f"{s.imp_string_a:.2f} A"
            })

        st.table(data)

    # ======================================================
    # 🔹 MPPT
    # ======================================================
    if corr and hasattr(corr, "mppt_detalle"):
        st.markdown("### ⚡ Nivel MPPT")

        data = []

        for i, m in enumerate(corr.mppt_detalle, start=1):
            data.append({
                "MPPT": i,
                "I operación": f"{m.i_operacion_a:.2f} A",
                "I diseño": f"{m.i_diseno_a:.2f} A"
            })

        st.table(data)

    # ======================================================
    # 🔹 INVERSOR DC
    # ======================================================
    if corr:
        st.markdown("### 🔌 Nivel Inversor DC")

        st.table({
            "Parámetro": ["Corriente DC", "Corriente diseño DC"],
            "Valor": [
                f"{corr.dc_total.i_operacion_a:.2f} A",
                f"{corr.dc_total.i_diseno_a:.2f} A"
            ]
        })

    # ======================================================
    # 🔹 AC
    # ======================================================
    if corr:
        st.markdown("### ⚡ Nivel AC")

        st.table({
            "Parámetro": ["Corriente AC", "Corriente diseño AC"],
            "Valor": [
                f"{corr.ac.i_operacion_a:.2f} A",
                f"{corr.ac.i_diseno_a:.2f} A"
            ]
        })

    # ======================================================
    # 🧵 CONDUCTORES
    # ======================================================
    if conductores and hasattr(conductores, "tramos"):

        st.markdown("### 🧵 Conductores")

        data = []

        tramos = conductores.tramos

        if hasattr(tramos, "dc") and tramos.dc:
            dc = tramos.dc
            data.append({
                "Tramo": "DC",
                "Calibre": f"{dc.calibre} AWG",
                "Ampacidad": f"{dc.ampacidad_ajustada_a:.2f} A",
                "I diseño": f"{dc.i_diseno_a:.2f} A",
                "VD (%)": f"{dc.vd_pct:.2f}"
            })

        if hasattr(tramos, "ac") and tramos.ac:
            ac = tramos.ac
            data.append({
                "Tramo": "AC",
                "Calibre": f"{ac.calibre} AWG",
                "Ampacidad": f"{ac.ampacidad_ajustada_a:.2f} A",
                "I diseño": f"{ac.i_diseno_a:.2f} A",
                "VD (%)": f"{ac.vd_pct:.2f}"
            })

        if data:
            st.table(data)

    # ======================================================
    # ⚠ PROTECCIONES
    # ======================================================
    if protecciones:

        st.markdown("### ⚠ Protecciones")

        # ---------------- AC ----------------
        st.markdown("#### 🔹 AC")
        st.table({
            "Parámetro": ["I diseño", "Breaker", "Norma"],
            "Valor": [
                f"{protecciones.ocpd_ac.i_diseno_a:.2f} A",
                f"{protecciones.ocpd_ac.tamano_a} A",
                protecciones.ocpd_ac.norma
            ]
        })

        # ---------------- DC ARRAY ----------------
        st.markdown("#### 🔹 DC (Array)")
        st.table({
            "Parámetro": ["I diseño", "Protección", "Norma"],
            "Valor": [
                f"{protecciones.ocpd_dc_array.i_diseno_a:.2f} A",
                f"{protecciones.ocpd_dc_array.tamano_a} A",
                protecciones.ocpd_dc_array.norma
            ]
        })

        # ---------------- FUSIBLE STRING ----------------
        st.markdown("#### 🔹 Fusible String")

        fus = protecciones.fusible_string

        st.table({
            "Parámetro": ["Requerido", "I diseño", "Fusible", "Norma"],
            "Valor": [
                "Sí" if fus.requerido else "No",
                f"{fus.i_diseno_a:.2f} A",
                f"{fus.tamano_a} A",
                fus.norma
            ]
        })

        # ---------------- MPPT ----------------
        if hasattr(protecciones, "mppt") and protecciones.mppt:

            st.markdown("#### 🔹 Protección por MPPT")

            data = []

            for i, p in enumerate(protecciones.mppt, start=1):
                data.append({
                    "MPPT": i,
                    "I diseño": f"{p.i_diseno_a:.2f} A",
                    "Protección": f"{p.tamano_a} A",
                    "Norma": p.norma
                })

            st.table(data)
