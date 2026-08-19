# SaaS-Ausbau Konzept

Dieses Dokument beschreibt, wie aus dem aktuellen Friseur-Scraper spaeter ein SaaS-Produkt werden koennte.

Wichtig: Das ist nur eine Konzept- und Vorgehens-Dokumentation. Es veraendert nicht die aktuelle Entwicklung und nicht den bestehenden Code-Ablauf.

## 1. Zielbild

Aus dem aktuellen Projekt koennte ein SaaS entstehen, das Unternehmen hilft, lokale Branchenstandorte zu finden, zu pruefen, anzureichern und als saubere Listen oder CRM-Daten zu nutzen.

Aktueller Fokus:

```text
Friseure und Barbershops in Deutschland
```

Spaeter denkbare weitere Branchen:

```text
Kosmetikstudios
Nagelstudios
Physiotherapie
Zahnaerzte
Restaurants
Autowerkstaetten
Fitnessstudios
Immobilienmakler
```

Der Kernnutzen waere:

- Standorte nach Branche und Region finden
- Duplikate reduzieren
- Datenqualitaet sichtbar machen
- Websites und E-Mail-Adressen ergaenzen
- Ergebnisse als Excel/CSV/API bereitstellen
- regelmaessige Updates anbieten
- Leads oder Standortdaten in andere Tools uebergeben

## 2. Sehr wichtiger Hinweis zu Google Places

Der aktuelle Scraper nutzt Google Places API (New) als Discovery-Quelle.

Fuer ein privates lokales Projekt ist das eine andere Situation als fuer ein SaaS, bei dem Kunden Zugriff auf Daten bekommen.

Vor einem echten SaaS-Start muss unbedingt rechtlich und vertraglich geprueft werden:

- Was darf aus Google Places gespeichert werden?
- Wie lange darf es gespeichert werden?
- Was darf Kunden angezeigt werden?
- Was darf exportiert werden?
- Welche Google-Attribution ist erforderlich?
- Gilt wegen EEA/Deutschland eine besondere Regelung?
- Darf das Produkt eine Datenbank aus Google-Places-Inhalten aufbauen?

Nach den offiziellen Google-Hinweisen gibt es Einschraenkungen bei Caching, Speicherung, Weitergabe und Darstellung von Places-Daten. Place IDs sind besonders behandelt und duerfen eher langfristig gespeichert werden, waehrend andere Places-Inhalte je nach Vertragslage eingeschraenkt sein koennen.

Praktische Konsequenz:

Ein SaaS sollte nicht einfach als "Google Places Datenbank zum Weiterverkaufen" geplant werden.

Besseres Zielbild:

- Google Places nur regelkonform als Live-/Lookup-Quelle nutzen
- Place IDs speichern
- eigene Enrichment-Daten sauber trennen
- Kundendaten getrennt speichern
- alternative oder lizenzierte Datenquellen pruefen
- vor Launch API-Nutzungsbedingungen und Datenschutz juristisch pruefen lassen

## 3. Moegliche SaaS-Positionierung

### Variante A: Leadlisten-SaaS

Kunden waehlen Branche und Region aus und erhalten eine bereinigte Liste.

Beispiel:

```text
Branche: Friseure
Region: Bayern
Output: Excel mit Firmenname, Adresse, Website, Telefon, E-Mail, Status
```

Vorteil:

- einfach zu verstehen
- schneller MVP moeglich

Risiko:

- starke rechtliche/API-Abhaengigkeit, wenn Daten aus Google Places stammen
- Listenverkauf kann datenschutz- und lizenzrechtlich kritisch sein

### Variante B: Datenqualitaets- und Enrichment-Tool

Kunden laden eigene Listen hoch. Das SaaS bereinigt, dedupliziert und ergaenzt diese Daten.

Beispiel:

```text
Kunde laedt CSV hoch
SaaS erkennt Duplikate
SaaS findet fehlende Websites
SaaS prueft E-Mail-Adressen
SaaS klassifiziert unklare Eintraege
```

Vorteil:

- Kundendaten stehen im Mittelpunkt
- Google kann eher als Lookup/Validierung statt als Datenbankquelle dienen
- hoeherer Business-Nutzen fuer Firmen

Risiko:

- mehr Produktlogik noetig
- Datenschutz und Auftragsverarbeitung werden wichtig

### Variante C: Monitoring-SaaS

Kunden beobachten Branchen, Regionen oder eigene Standorte ueber Zeit.

Beispiel:

```text
Neue Friseursalons in Berlin
geschlossene Standorte
neue Websites
neue Telefonnummern
fehlende E-Mail-Adressen
```

Vorteil:

- wiederkehrender Nutzen
- passt gut zu monatlichen SaaS-Abos

Risiko:

- regelmaessige Datenaktualisierung kostet Geld
- API- und Datenlizenzfragen muessen sauber geloest sein

### Empfehlung fuer den Start

Am sinnvollsten wirkt Variante B:

```text
Datenqualitaets- und Enrichment-SaaS fuer lokale Branchenlisten
```

Warum?

- weniger riskant als reiner Weiterverkauf fremder Daten
- klarer Nutzen fuer Kunden mit eigenen Daten
- vorhandene Projektlogik passt gut dazu
- spaeter kann Discovery/Monitoring dazukommen

## 4. Zielkunden

Moegliche Kunden:

- Vertriebsagenturen
- lokale Marketingagenturen
- Franchise-Unternehmen
- B2B-Sales-Teams
- Softwareanbieter fuer Terminbuchung
- CRM-Dienstleister
- Branchenportale
- Callcenter
- Unternehmensberater fuer lokale Betriebe

Typische Probleme dieser Kunden:

- Listen sind doppelt
- E-Mail-Adressen fehlen
- Websites fehlen
- Orte sind falsch geschrieben
- geschlossene Standorte sind noch enthalten
- mehrere Quellen widersprechen sich
- manuelle Pruefung kostet Zeit

## 5. Produktmodule

### Modul 1: Datenimport

Kunden koennen Daten hochladen.

Moegliche Formate:

```text
CSV
XLSX
Google Sheet
CRM-Export
API
```

Typische Spalten:

```text
firmenname
strasse
hausnummer
plz
ort
telefon
website
email
branche
quelle
```

### Modul 2: Datenvalidierung

Das System prueft:

- fehlen Pflichtfelder?
- ist die PLZ plausibel?
- ist die Telefonnummer normalisierbar?
- ist die Website erreichbar?
- ist die E-Mail formal korrekt?
- sind Koordinaten vorhanden?

Ergebnis:

```text
OK
Warnung
Fehler
Manuelle Pruefung
```

### Modul 3: Deduplizierung

Das System erkennt moegliche Duplikate.

Starke Signale:

- gleiche interne ID
- gleiche externe Place ID
- gleiche Adresse
- gleiche Telefonnummer
- sehr nahe Koordinaten
- sehr aehnlicher Name

Bewusst kein automatischer Merge nur wegen:

- gleicher Domain
- gleicher Haupt-E-Mail
- gleicher Franchise-Website

Warum?

Filialen koennen dieselbe Website haben, aber unterschiedliche physische Standorte sein.

### Modul 4: Enrichment

Das System ergaenzt fehlende Daten.

Moegliche Enrichment-Arten:

- Website finden
- E-Mail-Adresse finden
- Telefonnummer normalisieren
- Domain normalisieren
- Social-Media-Links finden
- Impressum pruefen
- Branchenhinweise erkennen
- Standortstatus pruefen

Wichtig:

Enrichment-Daten sollten immer mit Quelle und Zeitpunkt gespeichert werden.

Beispiel:

```text
email: info@example.de
email_quelle_url: https://example.de/impressum
email_confidence: 0.9
gefunden_am: 2026-08-19
```

### Modul 5: Klassifizierung

Das System entscheidet, in welche Liste ein Datensatz kommt.

Moegliche Klassen:

```text
komplett
manuelle_pruefung
aussortiert
```

Beispiel:

- klarer Friseur: `komplett`
- Beauty-Studio mit unklarer Leistung: `manuelle_pruefung`
- Autohaus: `aussortiert`
- dauerhaft geschlossen: `aussortiert`

### Modul 6: Manuelle Pruefung

Nicht alles sollte automatisch entschieden werden.

Ein SaaS braucht eine Oberflaeche, in der ein Mensch unsichere Eintraege pruefen kann.

Aktionen:

- akzeptieren
- aussortieren
- mit anderem Eintrag zusammenfuehren
- Daten korrigieren
- Notiz speichern
- Quelle markieren

### Modul 7: Export

Kunden wollen Ergebnisse weiterverwenden.

Moegliche Exporte:

```text
XLSX
CSV
Google Sheets
HubSpot
Salesforce
Pipedrive
API
Webhook
```

### Modul 8: Reports

Reports zeigen, wie gut ein Lauf war.

Beispiele:

- Anzahl Rohdaten
- Anzahl eindeutige Standorte
- Anzahl Duplikate
- Anzahl kompletter Datensaetze
- Anzahl manueller Prueffaelle
- Anzahl gefundener E-Mails
- Treffer je Suchbegriff
- Ueberschneidung je Suchbegriff
- Kosten pro Lauf
- Laufzeit pro Schritt

## 6. Benutzerrollen

### Owner

Besitzer des Accounts.

Darf:

- Zahlungsdaten verwalten
- Nutzer einladen
- Projekte loeschen
- API Keys verwalten

### Admin

Verwaltet Projekte und Daten.

Darf:

- Imports starten
- Exports starten
- Einstellungen aendern
- Teammitglieder verwalten

### Analyst

Arbeitet mit Daten.

Darf:

- Listen ansehen
- manuelle Pruefung bearbeiten
- Exporte erstellen

### Viewer

Nur Lesezugriff.

Darf:

- Reports ansehen
- Ergebnisse ansehen
- keine Daten veraendern

## 7. Wichtige SaaS-Seiten

### Login

Nutzer melden sich an.

### Dashboard

Zeigt:

- letzte Laeufe
- Datenqualitaet
- offene manuelle Pruefungen
- Exportstatus
- Kosten/Verbrauch

### Projekte

Ein Projekt koennte zum Beispiel sein:

```text
Friseure Deutschland
Friseure Berlin
Kundendaten Import August
```

### Import-Assistent

Schritte:

1. Datei hochladen
2. Spalten zuordnen
3. Vorschau pruefen
4. Import starten

### Lauf-Detailseite

Zeigt den Fortschritt eines Scraper-/Enrichment-Laufs.

Beispiele:

```text
Rohdaten geladen
Deduplizierung laeuft
Kontakt-Enrichment 348/1114 Websites
Excel-Export fertig
```

### Daten-Tabelle

Zeigt alle Standorte.

Funktionen:

- suchen
- filtern
- sortieren
- Spalten ein-/ausblenden
- Datensatz oeffnen
- manuell korrigieren

### Manuelle Pruefung

Spezielle Ansicht fuer unsichere Eintraege.

### Export-Center

Hier kann der Nutzer Exporte herunterladen oder Integrationen starten.

### Einstellungen

Enthaelt:

- Team
- Rollen
- API Keys
- Billing
- Datenaufbewahrung
- Quellen

## 8. Technische Zielarchitektur

Aktuell ist das Projekt ein lokales Python-Tool.

Ein SaaS braucht mehrere Schichten.

### Frontend

Das ist die Webseite, die Kunden benutzen.

Moegliche Technik:

```text
Next.js
React
Tailwind oder anderes UI-System
```

Aufgaben:

- Login
- Dashboard
- Tabellen
- Filter
- Uploads
- Fortschrittsanzeigen
- Export-Buttons

### Backend API

Das Backend nimmt Anfragen vom Frontend entgegen.

Moegliche Technik:

```text
FastAPI
Django
Node.js
```

Aufgaben:

- Nutzer pruefen
- Projekte verwalten
- Jobs starten
- Daten speichern
- Exporte bereitstellen

### Worker

Worker machen lange Aufgaben im Hintergrund.

Beispiele:

- Google Discovery
- Rohdaten-Verarbeitung
- Deduplizierung
- Website-Enrichment
- Excel-Export

Warum Worker?

Ein Website-Lauf kann Minuten oder Stunden dauern. Das darf nicht direkt im Browser warten.

### Job Queue

Eine Warteschlange fuer Aufgaben.

Moegliche Technik:

```text
Celery
RQ
Sidekiq
Cloud Tasks
BullMQ
```

Beispiel:

```text
User klickt "Enrichment starten"
Backend erstellt Job
Worker nimmt Job aus Queue
Worker schreibt Fortschritt
Frontend zeigt Fortschritt
```

### Datenbank

Speichert Accounts, Projekte, Standorte, Jobs und Ergebnisse.

Moegliche Technik:

```text
PostgreSQL
```

Warum PostgreSQL?

- stabil
- gut fuer Tabellen
- gut fuer Filter
- gut fuer SaaS
- spaeter mit PostGIS auch gut fuer Standortdaten

### Dateispeicher

Fuer Uploads und Exporte.

Moegliche Technik:

```text
S3
Cloudflare R2
Google Cloud Storage
```

Speichert:

- hochgeladene Dateien
- erzeugte XLSX-Dateien
- Reports

### Cache

Fuer schnelle Zwischenwerte und Rate Limits.

Moegliche Technik:

```text
Redis
```

## 9. Datenmodell grob

### Account

Ein Kunde oder Unternehmen.

Felder:

```text
id
name
plan
created_at
```

### User

Ein Nutzer.

Felder:

```text
id
account_id
email
name
role
created_at
```

### Project

Ein Datenprojekt.

Felder:

```text
id
account_id
name
branche
region
created_at
```

### Run

Ein einzelner Lauf.

Felder:

```text
id
project_id
type
status
started_at
finished_at
error_message
stats_json
```

### Location

Ein physischer Standort.

Felder:

```text
id
project_id
name
street
house_number
postcode
city
state
phone
website
email
status
classification
created_at
updated_at
```

### SourceRecord

Ein Rohdatensatz aus einer Quelle.

Felder:

```text
id
location_id
source_name
source_external_id
raw_json
collected_at
```

### SourceAttribution

Merkt sich, wo ein Feld herkommt.

Beispiel:

```text
location_id
field_name
value
source_name
source_url
confidence
collected_at
```

Warum wichtig?

Bei SaaS muss nachvollziehbar sein, woher Daten kommen.

## 10. Wichtige Workflows

### Workflow 1: Kunde laedt eigene Liste hoch

1. Kunde erstellt Projekt.
2. Kunde laedt CSV/XLSX hoch.
3. System erkennt Spalten.
4. Kunde bestaetigt Spaltenzuordnung.
5. System importiert Daten.
6. System normalisiert Namen, Adressen, Telefon, Website.
7. System erkennt Duplikate.
8. System sucht fehlende Kontaktinfos.
9. System klassifiziert Eintraege.
10. Kunde prueft unsichere Faelle.
11. Kunde exportiert Ergebnis.

### Workflow 2: Interner Branchenlauf

1. Admin waehlt Branche und Region.
2. System zeigt Kostenplan.
3. Admin bestaetigt bewusst.
4. Google Discovery startet.
5. Rohdaten werden gespeichert.
6. Deduplizierung laeuft.
7. Enrichment laeuft.
8. Klassifizierung laeuft.
9. Reports werden erzeugt.
10. Ergebnis wird fuer Nutzung freigegeben.

### Workflow 3: Wiederaufnahme nach Abbruch

1. Lauf wird unterbrochen.
2. Fertige Schritte bleiben in Checkpoints oder Job-Status erhalten.
3. Neuer Start liest vorhandene Fortschritte.
4. Fertige Google-Kacheln werden uebersprungen.
5. Fertige Websites werden uebersprungen.
6. Offene Schritte laufen weiter.

### Workflow 4: Manuelle Pruefung

1. System markiert unsichere Eintraege.
2. Nutzer sieht Grund der Unsicherheit.
3. Nutzer prueft Quelle oder Website.
4. Nutzer entscheidet:

```text
akzeptieren
aussortieren
zusammenfuehren
korrigieren
```

5. Entscheidung wird protokolliert.

## 11. SaaS-Betrieb

### Logging

Jeder Lauf sollte sichtbar machen:

- wann gestartet
- welcher Nutzer
- welches Projekt
- welche Quelle
- wie viele Rohdaten
- wie viele Fehler
- wie viele Exporte

### Monitoring

Das System sollte warnen bei:

- sehr vielen API-Fehlern
- stark steigenden Kosten
- ungewoehnlich langen Jobs
- vielen kaputten Websites
- fehlgeschlagenen Exporten

### Rate Limits

Wichtig fuer:

- Google API
- Website-Crawling
- Kunden-API
- Export-Erzeugung

### Kostenkontrolle

Vor kostenpflichtigen Laeufen sollte es immer eine Vorschau geben.

Beispiel:

```text
Geplante Google-Abfragen: 320
Geschaetzte Kosten ohne Free-Cap: 11,20 USD
Pagination/Splits koennen Zusatzkosten verursachen
```

Fuer SaaS wichtig:

- Kosten pro Account messen
- Limits pro Tarif setzen
- Warnungen senden
- teure Laeufe aktiv bestaetigen lassen

## 12. Sicherheit

Ein SaaS braucht andere Sicherheit als ein lokales Script.

Wichtig:

- Login mit sicheren Passwoertern oder SSO
- Rollen und Rechte
- Trennung von Kundendaten
- API Keys verschluesselt speichern
- Secrets nicht im Code
- HTTPS
- Backups
- Audit Logs
- Schutz vor Massendownloads
- Zugriff auf Exporte zeitlich begrenzen

## 13. Datenschutz

Dieses Thema muss vor einem echten Launch professionell geprueft werden.

Wichtige Punkte:

- Welche Daten sind personenbezogen?
- Sind E-Mail-Adressen personenbezogen?
- Gibt es Einzelunternehmer-Namen?
- Welche Rechtsgrundlage gibt es?
- Was steht in der Datenschutzerklaerung?
- Wie lange werden Daten gespeichert?
- Wie koennen Daten geloescht werden?
- Gibt es Auftragsverarbeitungsvertraege mit Kunden?
- Welche Unterauftragsverarbeiter werden genutzt?

Nach DSGVO-Grundprinzipien sollten Daten nur fuer klare Zwecke verarbeitet werden, nur so viel wie noetig gesammelt werden und nicht laenger als noetig gespeichert werden.

Praktisch fuer das Produkt:

- Datenquelle immer speichern
- Erfassungsdatum speichern
- Loeschkonzept bauen
- Exporthistorie protokollieren
- Kundendaten getrennt halten
- Impressum/Datenschutz fuer SaaS sauber erstellen lassen

## 14. API- und Datenquellenstrategie

Ein SaaS sollte nicht nur von einer Datenquelle abhaengen.

Moegliche Quellen:

- Kunden-Uploads
- eigene Website-Pruefung
- Google Places als regelkonformer Lookup
- Handelsregister-nahe Quellen, falls passend
- Branchenverzeichnisse mit Lizenz
- gekaufte/licensierte B2B-Daten
- oeffentliche Datenquellen, wenn erlaubt

Empfehlung:

Fuer den SaaS-Start zuerst Kundendaten importieren, bereinigen und enrichieren.

Discovery-Daten nur nach sauberer Lizenz- und Rechtspruefung als Produktfunktion anbieten.

## 15. MVP-Vorschlag

Ein MVP ist die kleinste sinnvolle Version, mit der echte Nutzer testen koennen.

### MVP-Ziel

```text
Kunde kann eine Standortliste hochladen, bereinigen, E-Mails finden und eine bessere Datei exportieren.
```

### MVP-Funktionen

- Login
- Projekt anlegen
- CSV/XLSX hochladen
- Spalten zuordnen
- Deduplizierung
- Website-/E-Mail-Enrichment
- manuelle Pruefliste
- XLSX/CSV Export
- einfacher Report

### Noch nicht im MVP

- Multi-Branchen-Discovery fuer alle Kunden
- CRM-Integrationen
- Zahlungsabrechnung
- grosse API
- Teamrollen im Detail
- komplexe Kartenansicht

## 16. Roadmap

### Phase 1: Produktklarheit

Ziel:

Verstehen, fuer wen das SaaS genau ist.

Aufgaben:

- Zielkunden festlegen
- 5 bis 10 potenzielle Nutzer sprechen
- wichtigstes Problem bestaetigen
- Beispiel-Inputdateien sammeln
- gewuenschte Exportformate klaeren
- rechtliche/API-Fragen sammeln

### Phase 2: Technisches Fundament

Ziel:

Aktuelles Script in wiederverwendbare Services aufteilen.

Aufgaben:

- Pipeline als Job lauffaehig machen
- Datenbankmodell erstellen
- Upload-Verarbeitung bauen
- Export-Service bauen
- Job-Status speichern
- Fehler und Logs pro Lauf speichern

### Phase 3: SaaS-MVP

Ziel:

Erster nutzbarer Web-Prototyp.

Aufgaben:

- Login
- Dashboard
- Projektseite
- Upload-Assistent
- Lauf-Fortschritt
- Ergebnis-Tabelle
- manuelle Pruefung
- Export

### Phase 4: Private Beta

Ziel:

Mit wenigen echten Nutzern testen.

Aufgaben:

- 3 bis 5 Kunden testen lassen
- manuelle Feedback-Runden
- Datenqualitaet messen
- Laufzeiten messen
- Kosten messen
- Datenschutztexte pruefen
- API-/Datenquellen-Nutzung pruefen

### Phase 5: Bezahltes Produkt

Ziel:

Aus Beta wird SaaS.

Aufgaben:

- Zahlungsmodell
- Tariflimits
- Rechnungen
- Teamverwaltung
- Support-Prozess
- Monitoring
- Backups
- Produktionsbetrieb

## 17. Preisideen

Moegliche Preislogik:

### Tarif nach Datensaetzen

Beispiel:

```text
Starter: 5.000 Datensaetze pro Monat
Pro: 50.000 Datensaetze pro Monat
Business: individuelle Menge
```

### Tarif nach Enrichment

Beispiel:

```text
pro gepruefter Website
pro gefundener E-Mail
pro verarbeitetem Standort
```

### Tarif nach Projekt

Beispiel:

```text
3 Projekte
20 Projekte
unbegrenzt
```

Empfehlung:

Am Anfang einfache Preise nutzen. Zu komplizierte Tarife machen Verkauf und Support schwer.

## 18. Risiken

### API-/Lizenzrisiko

Groesstes Risiko:

Daten aus Google Places duerfen moeglicherweise nicht so gespeichert, exportiert oder als SaaS-Datenprodukt verkauft werden, wie man es technisch koennte.

Massnahme:

- offizielle Google-Bedingungen pruefen
- gegebenenfalls Anwalt fragen
- Google-Inhalte von eigenen Daten trennen
- alternative Datenquellen vorbereiten

### Datenschutzrisiko

E-Mail-Adressen und Einzelunternehmerdaten koennen personenbezogen sein.

Massnahme:

- DSGVO-Konzept
- klare Zwecke
- Datenminimierung
- Loeschkonzept
- AV-Vertraege

### Kostenrisiko

Google API und Website-Crawling koennen Kosten verursachen.

Massnahme:

- Kosten vor Lauf anzeigen
- Limits setzen
- Abrechnung pro Account
- Warnungen

### Qualitaetsrisiko

Automatische Daten koennen falsch sein.

Massnahme:

- Confidence Scores
- Quellen anzeigen
- manuelle Pruefung
- keine unsicheren Merges erzwingen

### Betriebsrisiko

Jobs koennen abbrechen oder haengen.

Massnahme:

- Job Queue
- Checkpoints
- Retry-Logik
- Timeouts
- Monitoring

## 19. Was vom aktuellen Projekt wiederverwendbar ist

Gut wiederverwendbar:

- Google Discovery Grundlogik
- Keyword-Provenienz
- Deduplizierung
- Normalisierung
- Relevanzbewertung
- E-Mail-Enrichment
- Excel-Export
- Kostenplanung
- Checkpoint-Ideen

Muss fuer SaaS umgebaut werden:

- lokale Dateien zu Datenbank
- Terminal-Befehle zu Web-UI
- direkte Laeufe zu Hintergrundjobs
- lokale Checkpoints zu Job-State
- lokale Excel-Dateien zu Download-Artefakten
- ein Nutzer zu Multi-Tenant Accounts

## 20. Empfohlene naechste Schritte

### Schritt 1: Produktentscheidung

Entscheide, welche SaaS-Variante zuerst gebaut werden soll.

Empfehlung:

```text
Upload + Bereinigung + Enrichment + Export
```

### Schritt 2: Rechtliche Vorpruefung

Vor allem klaeren:

- Google Places Nutzung
- Speicherung von Places-Daten
- Export an Kunden
- E-Mail-Enrichment
- DSGVO

### Schritt 3: MVP-Skizze

Eine einfache Web-App planen:

- Dashboard
- Upload
- Laufstatus
- Tabelle
- manuelle Pruefung
- Export

### Schritt 4: Datenmodell definieren

Vor dem Programmieren klaeren:

- welche Tabellen
- welche Felder
- welche Quellen
- welche Kunden-Trennung

### Schritt 5: Kleine Beta

Mit wenigen echten Nutzern testen, bevor viel gebaut wird.

## 21. Ein moeglicher SaaS-Satz

Kurzbeschreibung fuer Kunden:

```text
Wir bereinigen lokale Branchenlisten, entfernen Duplikate, ergaenzen Websites und E-Mail-Adressen und liefern exportierbare, nachvollziehbare Standortdaten fuer Vertrieb und Marketing.
```

Noch kuerzer:

```text
Saubere lokale B2B-Standortdaten aus chaotischen Listen.
```

## 22. Quellen und Pruefpunkte

Diese Quellen wurden fuer die rechtlichen/API-Hinweise geprueft. Sie ersetzen keine Rechtsberatung, helfen aber bei der Orientierung.

- Google Places API Policies und Attribution: https://developers.google.com/maps/documentation/places/web-service/policies
- Google Maps Platform Service Specific Terms: https://cloud.google.com/maps-platform/terms/maps-service-terms
- Google Maps Platform EEA Places API Permitted Uses: https://cloud.google.com/terms/maps-platform/eea-places-api-permitted-uses
- Google Places API Anpassungen fuer EEA-Kunden: https://developers.google.com/maps/comms/eea/places
- DSGVO-Grundprinzipien der Europaeischen Kommission: https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/principles-gdpr_en

