# paleocirc
API web scraping per ottenere circolari dal sito dell'I.T.I.S. Paleocapa di Bergamo

## Installazione
Per installare questa libreria è necessario eseguire ```pip install paleocirc``` in un terminale.

## Ricavare informazioni di una circolare
Puoi ottenere le informazioni di una circolare utlizzando<br>
```
from paleocirc import Circolari

circolari = Circolari()
circolare = circolari.get(numero_circolare)

circolare.number      #stringa: numero circolare (ad esempio 21, 250 bis)
circolare.name        #stringa: nome della circolare
circolare.date        #stringa: data in cui la circolare è uscita
circolare.url         #stringa: URL che porta alla pagina della circolare (non al pdf)
circolare.restricted  #bool: True se la circolare è solo per i membri dello staff, altrimenti False

```

## Scaricare una circolare
È anche possibile scaricare le circolari utilizzando:<br>
```
from paleocirc import Circolari

circolari = Circolari()
circolare = circolari.get(numero_circolare)

circolare.download(
  percorso_file,     #stringa: obbligatorio, la cartella in cui verrà scaricata la circolare (esempio: 'circolari')
  filename=filename  #stringa: opzionale, default: circolare.number. il nome con cui verrà salvata la circolare
)
```

## Note
Questa libreria è molto lenta a recupare circolari (4s ai 10s circa per circolare). Questo è dovuto al fatto che il sito da cui vengono prese (https://itispaleocapa.edu.it/circolari) non ha un API, ma per prendere informazioni è necessario fare web scraping.
