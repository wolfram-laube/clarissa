// BLAUWEISS Rechnung - Januar 2026 - nemensis AG
// Generated from: 2026-01_timesheet_nemensis_de.typ

#let invoice(
  invoice_number: "AR_001_2026",
  invoice_date: "03. Januar 2026",
  client_name: "Kunde GmbH",
  client_address: "Musterstraße 123",
  client_city: "D - 12345 Musterstadt",
  client_reg_id: "",
  client_vat_id: "",
  contract_number: "00003151",
  remote_hours: 0,
  remote_rate: 105,
  onsite_hours: 0,
  onsite_rate: 120,
  logo_path: "logo.jpg",
) = {
  // Colors
  let bw_blue = rgb("#00aeef")
  let bw_green = rgb("#8dc63f")
  let bw_gray = rgb("#808080")
  let table_head = rgb("#d5e8f0")
  let alert_bg = rgb("#fff8dc")

  // Calculate totals
  let remote_amount = remote_hours * remote_rate
  let onsite_amount = onsite_hours * onsite_rate
  let total = remote_amount + onsite_amount

  set document(title: "Rechnung " + invoice_number, author: "BlauWeiss EDV LLC")
  set page(
    paper: "a4",
    margin: (top: 2.5cm, bottom: 2cm, left: 2cm, right: 2cm),
    footer: context [
      #set text(size: 8pt, fill: bw_gray)
      #grid(
        columns: (1fr, 1fr, 1fr),
        align: (left, center, right),
        [BlauWeiss EDV LLC],
        [Rechnung #invoice_number],
        [Seite #counter(page).display() von #counter(page).final().first()],
      )
    ]
  )
  set text(font: "Poppins", size: 10pt)

  // Header with logo
  grid(
    columns: (1fr, auto),
    align: (left, right),
    [
      #text(size: 18pt, weight: "bold", fill: bw_blue)[BlauWeiss]
      #text(size: 18pt, weight: "bold", fill: bw_green)[EDV LLC]
    ],
    image(logo_path, width: 3cm)
  )

  v(0.3cm)

  // Company info
  text(size: 8pt, fill: bw_gray)[
    17100 Bear Valley Ln · Houston · TX 77084 · USA \
    wolfram\@blauweiss-edv.com · +1 (832) 787-1668 · VAT: 98-1635491
  ]

  v(0.8cm)

  // Client address block
  grid(
    columns: (1fr, 1fr),
    [
      text(size: 8pt, fill: bw_gray)[An:] \
      text(weight: "bold")[#client_name] \
      client_address \
      client_city \
      #if client_reg_id != "" [#client_reg_id \ ]
    ],
    align(right)[
      #set text(size: 9pt)
      #table(
        columns: 2,
        stroke: none,
        inset: 3pt,
        [Rechnungsnummer:], [*#invoice_number*],
        [Rechnungsdatum:], [#invoice_date],
        [Auftragsnummer:], [#contract_number],
      )
    ]
  )

  v(1cm)

  // Title
  text(size: 14pt, weight: "bold")[Rechnung]

  v(0.5cm)

  [Sehr geehrte Damen und Herren,]

  v(0.3cm)

  [für unsere Beratungsleistungen zur Vertragsnummer #contract_number erlauben wir uns, folgenden Betrag in Rechnung zu stellen:]

  v(0.5cm)

  // Invoice table
  table(
    columns: (1fr, auto, auto, auto),
    inset: 8pt,
    align: (left, center, right, right),
    fill: (_, y) => if y == 0 { table_head } else { none },
    table.header(
      [*Beschreibung*], [*Menge*], [*Einzelpreis*], [*Betrag*]
    ),
    [Beratungsleistung remote], [#remote_hours Ph], [à EUR #remote_rate], [EUR #remote_amount],
    [Beratungsleistung on-site], [#onsite_hours Ph], [à EUR #onsite_rate], [EUR #onsite_amount],
    table.cell(colspan: 3, align: right)[*Gesamt (netto)*], [*EUR #total*],
  )

  v(0.3cm)

  text(size: 9pt, fill: bw_gray)[
    Kein Ausweis von Umsatzsteuer – Leistungsempfänger schuldet die Steuer \
    #if client_vat_id != "" [Kunden-USt-IdNr.: #client_vat_id]
  ]

  v(0.5cm)

  [Wir bedanken uns für das Vertrauen, die gute Zusammenarbeit und sehen der Begleichung des Rechnungsbetrages unter den vereinbarten Zahlungsbedingungen an die genannte Bankverbindung entgegen.]

  v(0.3cm)

  [Für die gegenständliche Rechnung:]
  list[3% Skonto bei Sofortzahlung (1-2 Tage)]

  v(0.3cm)

  [Mit freundlichen Grüßen,]

  v(1.5cm)

  line(length: 6cm)
  [Autorisierte Unterschrift]

  v(0.5cm)

  text(weight: "bold")[Anlage:]
  list[Leistungsschein][Digitale Signatur]
}

// =====================================================
// RECHNUNG für nemensis AG Deutschland - Januar 2026
// Basierend auf Timesheet: 2026-01_timesheet_nemensis_de.typ
// Stunden: 184h remote @ EUR 105
// =====================================================

#invoice(
  invoice_number: "AR_001_2026",
  invoice_date: "03. Januar 2026",
  client_name: "nemensis AG Deutschland",
  client_address: "Alter Wall 69",
  client_city: "D - 20457 Hamburg",
  client_reg_id: "HRB. NR.: 181535 Hamburg",
  client_vat_id: "DE310161615",
  contract_number: "00003153",
  remote_hours: 184,
  remote_rate: 105,
  onsite_hours: 0,
  onsite_rate: 120,
)
