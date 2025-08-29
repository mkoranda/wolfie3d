:joystick: Oppgavebank – Vibe Wolf 3D
 Alle starter med samme repo (koden dere har nå).
 Plukk oppgaver dere synes er morsomme – målet er å eksperimentere og “vibe-kode”.
 Flere grupper kan gjøre samme oppgave – vi samler kode etterpå.
:dart: Core Gameplay
 Fiende HP: Fienden tåler flere skudd (f.eks. 3) før den dør.
 Spiller HP: Spilleren har helse. Når en fiende kommer nær, tar du skade.
 Game Over: Vis en enkel “Game Over”-melding når spilleren dør.
 Score: +100 poeng per fiende drept. Vis scoren på skjermen.
:gun: Våpen & ammo
 Ammo-teller: Legg til ammo. Når du går tom, kan du ikke skyte.
 Reload: Trykk R for å fylle opp ammo igjen.
 Pickup-objekt: Lag et “ammo-box”-sprite på gulvet som kan plukkes opp.
:japanese_ogre: Fiender
 Flere fiender: Legg inn flere fiender på kartet.
 Forskjellige fiender: To typer med ulik fart eller HP.
 Fiende-animasjon: Bytt mellom to sprites for å få en enkel gå-animasjon.
 Dødsanimasjon: Når fienden dør, vis en annen sprite i et kort øyeblikk.
:checkered_flag: Checkpoints & mål
 Checkpoints: Legg til punkter i kartet spilleren må gå innom.
 Seier: Når alle fiender er drept eller alle checkpoints er tatt → vis “You win!”.
 Timer: Mål tiden fra start til seier.
 Highscore: Kombiner tid og score i en enkel “highscore”-beregning.
:compass: Verden & interaksjon
 Dør/port: Lag en vegg som kan åpnes med en tast.
 Nøkkel: Legg til et nøkkelobjekt – nødvendig for å åpne døren.
 Secret room: Skjul et rom bak en vegg som kan åpnes.
 Pickup helse: Legg inn helsepakke som gir +50 HP.
:art: Presentasjon
 Lys/fog: Vegger og fiender blir mørkere jo lenger unna de er.
 Mini-map forbedring: Vis fiender og checkpoints som små prikker.
 HUD: Vis HP, ammo og score med enkel overlay.
 Lyd: Legg på skuddlyd eller fiende-lyd (pygame.mixer).
:rocket: Ekstra / Stretch Goals
 Granat/rocket: Skyt et prosjektil som gjør skade i radius.
 Flere våpen: Bytt mellom pistol og maskingevær.
 Multiplayer-lite: Synk posisjon til to spillere over nettverk (enkelt UDP).
 Level-loader: Les kartet fra en .json- eller .txt-fil i stedet for hardkodet MAP.
