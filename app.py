import json
import os
from datetime import datetime
import streamlit as st

# Nastavení vzhledu aplikace
st.set_page_config(
    page_title="KB montážní kalendář",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DB_FILE = "databaze_zakazek.json"
ZAMESTNANCI = ["Luboš", "Maty", "Jirka", "Zdenda", "Franta", "Honza S."]


def nacti_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def uloz_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if "zakazky" not in st.session_state:
    st.session_state.zakazky = nacti_data()


def vypocti_zbyvajici_cas(termin_str):
    try:
        termin = datetime.strptime(termin_str, "%Y-%m-%d %H:%M")
        nyni = datetime.now()
        rozdil = termin - nyni
        if rozdil.total_seconds() <= 0:
            return "❌ PO TERMÍNU!"
        dny = rozdil.days
        hodiny = rozdil.seconds // 3600
        minuty = (rozdil.seconds % 3600) // 60
        if dny > 0:
            return f"⏳ {dny} dní, {hodiny} hod"
        return f"⏳ {hodiny} hod, {minuty} min"
    except:
        return "Neznámý termín"


# --- MODERNÍ TRELLO-LIKE DESIGN POMOCÍ CSS ---
st.markdown(
    """
    <style>
    .stApp { background-color: #f1f2f4; }
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    .trello-form {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24); margin-bottom: 20px;
    }
    .trello-karta {
        background-color: #ffffff; padding: 16px; border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 16px; border-left: 6px solid #0055cc;
    }
    .trello-karta-hotovo {
        background-color: #ffffff; padding: 16px; border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 16px; border-left: 6px solid #1f845a;
    }
    .badge-zeleny {
        background-color: #e3fcef; color: #1f845a; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;
    }
    .badge-fialovy {
        background-color: #eae6ff; color: #403294; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;
    }
    .badge-tym {
        background-color: #dfe1e6; color: #172b4d; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("📋 KB montážní kalendář")
sloupec_form, sloupec_prehled = st.columns(2)

# ================= VLEVO: FORMULÁŘ =================
with sloupec_form:
    st.markdown('<div class="trello-form">', unsafe_allow_html=True)
    st.subheader("➕ Nová zakázka")

    nazev = st.text_input("Název zakázky / Klient:")
    typ_prace = st.selectbox(
        "Typ práce:", ["Montáže", "Výroba a montáž 3D log"]
    )
    hlavni_pracovnici = st.multiselect("Přiřadit tým:", ZAMESTNANCI)

    col1, col2 = st.columns(2)
    with col1:
        datum = st.date_input("Termín - Datum:")
    with col2:
        cas = st.time_input("Termín - Čas:")

    if st.button("Uložit do nástěnky", use_container_width=True, type="primary"):
        if not nazev.strip():
            st.error("Zadejte název!")
        elif not hlavni_pracovnici:
            st.error("Vyberte pracovníky!")
        else:
            # Výchozí přiřazení pro první uložení úkolů (vezme se první člověk z vybraného týmu)
            vychozi_clovek = hlavni_pracovnici[0]

            if typ_prace == "Montáže":
                faze = {
                    "Příprava": {"hotovo": False, "kdo": vychozi_clovek},
                    "Montáž": {"hotovo": False, "kdo": vychozi_clovek},
                }
            else:
                faze = {
                    "Modelování": {"hotovo": False, "kdo": vychozi_clovek},
                    "3D tisk": {"hotovo": False, "kdo": vychozi_clovek},
                    "Fréza a laser": {"hotovo": False, "kdo": vychozi_clovek},
                    "Příprava elektriky": {"hotovo": False, "kdo": vychozi_clovek},
                    "Kompletace": {"hotovo": False, "kdo": vychozi_clovek},
                    "Montáž": {"hotovo": False, "kdo": vychozi_clovek},
                }

            termin_komplet = f"{datum} {cas.strftime('%H:%M')}"
            nova_zakazka = {
                "id": len(st.session_state.zakazky) + 1,
                "nazev": nazev,
                "hlavni_pracovnici": hlavni_pracovnici,
                "typ": typ_prace,
                "datum_zadani": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "termin": termin_komplet,
                "faze": faze,
            }
            st.session_state.zakazky.append(nova_zakazka)
            uloz_data(st.session_state.zakazky)
            st.success("Zakázka vytvořena!")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ================= VPRAVO: NÁSTĚNKA ZAKÁZEK =================
with sloupec_prehled:
    st.subheader("🗂️ Aktivní karty zakázek")

    if not st.session_state.zakazky:
        st.info("Žádné zakázky na nástěnce.")
    else:
        for idx, zakazka in enumerate(list(st.session_state.zakazky)):
            vse_hotovo = all(
                info["hotovo"] for info in zakazka["faze"].values()
            )
            stav_casu = (
                "✅ HOTOVO"
                if vse_hotovo
                else vypocti_zbyvajici_cas(zakazka["termin"])
            )

            styl_karty = (
                "trello-karta-hotovo" if vse_hotovo else "trello-karta"
            )
            stitok_typu = (
                "badge-zeleny"
                if zakazka["typ"] == "Montáže"
                else "badge-fialovy"
            )
            tým_str = ", ".join(zakazka["hlavni_pracovnici"])

            st.markdown(
                f"""
                <div class="{styl_karty}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span class="{stitok_typu}">{zakazka['typ']}</span>
                        <span style="font-size: 0.75rem; color: #6b778c;">Zadáno: {zakazka['datum_zadani']}</span>
                    </div>
                    <h3 style="margin: 0 0 10px 0; color: #172b4d; font-size: 1.35rem;">{zakazka['nazev']}</h3>
                    <div style="margin-bottom: 10px;">
                        <span style="font-size: 0.85rem; color: #44546f;">Tým:</span>
                        <span class="badge-tym">{tým_str}</span>
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

            c_cas, c_smazat = st.columns(2)
            with c_cas:
                if "❌" in stav_casu:
                    st.markdown(
                        f"**Stav:** <span style='color:#ae2e24; font-weight:bold;'>{stav_casu}</span>",
                        unsafe_allow_html=True,
                    )
                elif "✅" in stav_casu:
                    st.markdown(
                        f"**Stav:** <span style='color:#1f845a; font-weight:bold;'>{stav_casu}</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"**Termín:** <span style='color:#d97706; font-weight:bold;'>{stav_casu}</span>",
                        unsafe_allow_html=True,
                    )
            with c_smazat:
                if st.button("🗑️ Smazat kartu", key=f"del_{idx}"):
                    st.session_state.zakazky.pop(idx)
                    uloz_data(st.session_state.zakazky)
                    st.rerun()

            zmena = False
            with st.expander("📝 Otevřít úkoly a rozdělení práce"):
                for faze_nazev, info in zakazka["faze"].items():
                    col_chk, col_kdo = st.columns(2)

                    # Checkbox pro splnění dílčí fáze
                    novy_stav = col_chk.checkbox(
                        faze_nazev,
                        value=info["hotovo"],
                        key=f"chk_{idx}_{faze_nazev}",
                    )
                    if novy_stav != info["hotovo"]:
                        zakazka["faze"][faze_nazev]["hotovo"] = novy_stav
                        zmena = True

                    # Výběr konkrétního pracovníka z přiděleného týmu
                    if info["kdo"] in zakazka["hlavni_pracovnici"]:
                        index_pracovnika = zakazka[
                            "hlavni_pracovnici"
                        ].index(info["kdo"])
                    else:
                        index_pracovnika = 0

                    novy_kdo = col_kdo.selectbox(
                        "Odpovědný:",
                        options=zakazka["hlavni_pracovnici"],
                        index=index_pracovnika,
                        key=f"kdo_{idx}_{faze_nazev}",
                        label_visibility="collapsed",
                    )
                    if novy_kdo != info["kdo"]:
                        zakazka["faze"][faze_nazev]["kdo"] = novy_kdo
                        zmena = True

                if zmena:
                    uloz_data(st.session_state.zakazky)
                    st.rerun()