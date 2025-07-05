# Időkép Home Assistant integráció

Ez a Home Assistant egyéni integráció az Időkép időjárás szolgáltatás adatait jeleníti meg szenzorok és időjárás entitás formájában, támogatva az óránkénti és napi előrejelzést is.

## Telepítés HACS-on keresztül

1. **Hozzáadás a HACS-hoz:**
   - Nyisd meg a Home Assistantot böngészőben.
   - Navigálj a **HACS** menüponthoz.
   - Kattints a jobb felső sarokban a **⋮** gombra és válaszd az **Egyedi repók** menüpontot.
   - Add hozzá a GitHub repó URL-jét ehhez a tárolóhoz: `https://github.com/FabianGabor/HA-Idokep`
   - Válaszd ki a típusnál az `Integráció` (Integration) lehetőséget.

2. **Telepítés:**
   - A HACS főoldalán keresd meg az „Időkép” integrációt a listában.
   - Kattints rá, majd válaszd a **Telepítés** gombot.
   - A telepítés után indítsd újra a Home Assistantot.

3. **Beállítás:**
   - Újraindítás után menj a **Beállítások > Eszközök és szolgáltatások > Integrációk** menüpontra.
   - Kattints a jobb alsó sarokban a **+ HOZZÁADÁS** gombra, majd keresd meg az „Időkép” integrációt.
   - Add meg a kívánt helyszínt (pl. város vagy település neve), majd fejezd be a beállítást.

## Funkciók
- Jelenlegi időjárás, óránkénti és 30 napos napi előrejelzés
- Home Assistant időjárás entitás támogatás (új forecast API)
- Magyar időjárási állapotok helyes leképezése
- Szenzorok minden elérhető adatkulcshoz

## Hibák, fejlesztés
Ha hibát találsz vagy javaslatod van, nyiss egy issue-t a GitHub repóban!

## 🧪 Fejlesztők számára

- **Gyors tesztelés**: Lásd [FAST_TESTING_GUIDE.md](FAST_TESTING_GUIDE.md) a gyors fejlesztői workflow-hoz
- **Teljes tesztelés**: Lásd [TEST_RUNNER_GUIDE.md](TEST_RUNNER_GUIDE.md) a részletes tesztelési útmutatóhoz
- **Optimalizált workflow**: Lásd [OPTIMIZED_WORKFLOW_GUIDE.md](OPTIMIZED_WORKFLOW_GUIDE.md)
