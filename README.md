genregrabber
============

Search Wikipedia for given band names and collect their genre, founding year, and origin country.

Useful, e.g., for adding approximate information about bands' genres to a [running order](https://github.com/n-st/running-order-TEMPLATE). ;)

Example usage
-------------

```
% echo 'raised fist' | python genregrabber-multiwiki.py
raised fist; ERROR: No band information in "Luleå" on cs.wikipedia.org. (https://cs.wikipedia.org/wiki/Lule%C3%A5)
Raised Fist; Hardcore Punk + Post-Hardcore + New School Hardcore; SE/Schweden; 1993; https://de.wikipedia.org/wiki/Raised%20Fist
Raised Fist; Hardcore punk; SE/Sweden; 1993; https://en.wikipedia.org/wiki/Raised%20Fist
```
