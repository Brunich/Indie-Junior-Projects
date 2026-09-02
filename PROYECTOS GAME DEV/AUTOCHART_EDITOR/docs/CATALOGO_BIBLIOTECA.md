# Catalogo de la biblioteca — las 396 por calidad medida

Generado por `tools/catalogo_md.py` sobre `datos/corpus_oro.json`. 360 pistas de guitarra en Experto con al menos 400 notas, medidas con `atlas.escanear` — la misma funcion que alimenta `atlas_patrones.json`.

## Los cuatro filtros

Los umbrales no son una opinion: salen de los percentiles de esta misma biblioteca.

| Filtro | Falla si | Umbral | Cuantas caen |
|---|---|---|---|
| **machacona** | repite traste demasiado | > p75 = 43.3% | 90 |
| **vacia** | casi no tocas | < p25 = 3.13 notas/s | 90 |
| **poco vocabulario** | usa pocos gestos distintos | < p50 = 0.48 | 180 |
| **no respira** | densidad plana de principio a fin | < p50 = 2.81 | 178 |

**Pasan los cuatro: 38 de 360 (11 %).**

Lo que mas se cae es *vocabulario* y *contraste*, no la repeticion. Es decir: el chart medio de la biblioteca no es machacon, es **plano** — toca siempre lo mismo con la misma intensidad. Eso es exactamente lo que un generador tiende a producir solo, asi que es la trampa a vigilar.

## Indice

- [Oro — la vara del generador](#oro) — 38
- [Buenas — fallan un solo filtro](#buenas) — 121
- [Machaconas pero te gustan](#machaconas-pero-te-gustan) — 62
- [Correctas — cumplen, sin mas](#correctas) — 62
- [Machaconas y prescindibles](#machaconas-y-prescindibles) — 16
- [Vacias — casi no tocas](#vacias) — 61

## Oro — la vara del generador

Pasan los cuatro filtros. Ni machaconas, ni vacias, con vocabulario por encima de la mediana y con contraste: la cancion respira. Son estas las que el generador tiene que querer parecerse.

**38 canciones.**

| Cancion | Artista | Notas | n/s | Repite | Vocab. | Respira | Falla |
|---|---|---:|---:|---:|---:|---:|---|
| Steve Ouimette - The Devil Went Down to Georgia | Steve Ouimette | 2398 | 6.33 | 22% | 0.72 | 79.23 | — |
| Wintersun - Beautiful Death | Wintersun | 2556 | 5.33 | 35% | 0.85 | 7.11 | — |
| Slayer - Raining Blood | Slayer | 1271 | 6.24 | 33% | 0.62 | 20.46 | — |
| Los Romanticos De Zacatecas - Muchacha | Los Romanticos De Zacatecas | 614 | 3.66 | 11% | 0.72 | 7.05 | — |
| Avenged Sevenfold (WaveGroup) - Beast And the Harlot | Avenged Sevenfold (WaveGroup) | 1683 | 5.00 | 43% | 0.73 | 6.07 | — |
| Arctic Monkeys - Fireside | Arctic Monkeys | 709 | 4.10 | 12% | 0.92 | 4.57 | — |
| Def Leppard - Rock of Ages (Live) | Def Leppard | 1031 | 3.55 | 11% | 0.60 | 9.91 | — |
| AC_DC - Thunderstruck | AC/DC | 1297 | 4.42 | 12% | 0.69 | 5.93 | — |
| Gerard Marino - The End Begins (To Rock) | Gerard Marino | 945 | 3.87 | 11% | 0.61 | 8.40 | — |
| Joe Satriani - Satch Boogie | Joe Satriani | 1288 | 7.02 | 2% | 0.74 | 4.14 | — |
| The Hellacopters - I'm In The Band | The Hellacopters | 717 | 3.81 | 31% | 0.63 | 4.69 | — |
| Ozzy Osbourne - Mr. Crowley | Ozzy Osbourne | 1123 | 3.51 | 11% | 0.50 | 9.65 | — |
| Heart (WaveGroup) - Crazy on You | Heart (WaveGroup) | 1082 | 3.88 | 18% | 0.65 | 3.52 | — |
| Marilyn Manson - Putting Holes In Happiness | Marilyn Manson | 1297 | 5.92 | 12% | 0.48 | 15.25 | — |
| Metallica - Welcome Home (Sanitarium) | Metallica | 1444 | 3.78 | 30% | 0.54 | 4.38 | — |
| Steve Vai - For the Love of God | Steve Vai | 1359 | 3.85 | 14% | 0.48 | 8.66 | — |
| An Endless Sporadic - Impulse | An Endless Sporadic | 1055 | 4.23 | 17% | 0.48 | 7.74 | — |
| The Police (WaveGroup) - Message In A Bottle | The Police (WaveGroup) | 977 | 3.32 | 8% | 0.68 | 2.86 | — |
| Alpha Legion - Evil Force | Alpha Legion | 1449 | 4.75 | 13% | 0.54 | 3.93 | — |
| Velvet Revolver - She Builds Quick Machines | Velvet Revolver | 854 | 3.55 | 9% | 0.54 | 3.96 | — |
| Queen - Fat Bottomed Girls | Queen | 841 | 3.59 | 19% | 0.62 | 2.97 | — |
| Hellacopters - I'm in the Band | Hellacopters | 724 | 3.85 | 30% | 0.53 | 3.90 | — |
| Deftones - Hole in the Earth | Deftones | 941 | 3.64 | 18% | 0.55 | 3.44 | — |
| Living Colour - Cult of Personality | Living Colour | 1382 | 5.00 | 4% | 0.62 | 2.81 | — |
| Mastodon - Sleeping Giant | Mastodon | 1481 | 4.42 | 13% | 0.53 | 3.60 | — |
| L70ETC - I Am Murloc | L70ETC | 806 | 3.88 | 27% | 0.49 | 4.72 | — |
| White Zombie (WaveGroup) - Black Sunshine | White Zombie (WaveGroup) | 994 | 4.32 | 25% | 0.48 | 5.01 | — |
| Dope - Nothing For Me Here | Dope | 941 | 5.53 | 20% | 0.58 | 2.82 | — |
| Reverend Horton Heat (WaveGroup) - Psychobilly Freakout | Reverend Horton Heat (WaveGroup) | 717 | 4.71 | 32% | 0.48 | 4.63 | — |
| Buckethead - Soothsayer | Buckethead | 2236 | 4.14 | 20% | 0.50 | 3.93 | — |
| Gallows - In The Belly Of A Shark | Gallows | 738 | 4.72 | 13% | 0.50 | 3.88 | — |
| Matchbook Romance - Monsters | Matchbook Romance | 1091 | 4.69 | 12% | 0.53 | 3.12 | — |
| Dream Theater - Pull Me Under | Dream Theater | 1784 | 3.66 | 26% | 0.49 | 3.96 | — |
| Junior H - Dias Nublados | Junior H | 919 | 4.25 | 24% | 0.52 | 2.92 | — |
| Bret Michaels Band - Go That Far | Bret Michaels Band | 849 | 5.01 | 26% | 0.51 | 3.12 | — |
| Ozzy Osbourne - Crazy Train | Ozzy Osbourne | 1384 | 4.94 | 42% | 0.53 | 2.85 | — |
| Lamb of God (WaveGroup) - Laid To Rest | Lamb of God (WaveGroup) | 1268 | 5.61 | 12% | 0.52 | 2.84 | — |
| The Sleeping - Don't Hold Back | The Sleeping | 885 | 3.45 | 14% | 0.50 | 2.99 | — |

## Buenas — fallan un solo filtro

A un paso del oro. Utiles como referencia de segunda linea.

**121 canciones.**

| Cancion | Artista | Notas | n/s | Repite | Vocab. | Respira | Falla |
|---|---|---:|---:|---:|---:|---:|---|
| Arctic Monkeys - Knee Socks | Arctic Monkeys | 506 | 2.19 | 21% | 0.78 | 33.70 | vacia |
| Tom Morello - Guitar Battle vs. Tom Morello | Tom Morello | 496 | 3.11 | 24% | 0.65 | 9.51 | vacia |
| Steve Ouimette - Top Gun Anthem | Steve Ouimette | 706 | 2.71 | 12% | 0.70 | 7.40 | vacia |
| Nirvana - Smells Like Teen Spirit | Nirvana | 857 | 2.98 | 39% | 0.70 | 7.11 | vacia |
| Tame Impala - The Less I Know the Better | Tame Impala | 422 | 1.99 | 1% | 0.74 | 5.34 | vacia |
| La Bande-Son Imaginaire - Los Bastardos | La Bande-Son Imaginaire | 489 | 2.04 | 9% | 0.63 | 6.31 | vacia |
| Black Sabbath (WaveGroup) - War Pigs | Black Sabbath (WaveGroup) | 1117 | 2.50 | 19% | 0.57 | 9.33 | vacia |
| Danzig (WaveGroup) - Mother | Danzig (WaveGroup) | 625 | 3.05 | 5% | 0.61 | 6.57 | vacia |
| Foreigner - Jukebox Hero | Foreigner | 663 | 2.86 | 35% | 0.54 | 11.25 | vacia |
| Caos - La Planta | Caos | 680 | 2.83 | 33% | 0.59 | 5.53 | vacia |
| Guns N' Roses - November Rain | Guns N' Roses | 803 | 1.77 | 8% | 0.53 | 13.97 | vacia |
| Def Leppard - Photograph (Live) | Def Leppard | 802 | 2.61 | 10% | 0.57 | 5.76 | vacia |
| KISS (Steve Ouimette) - Rock & Roll All Nite | KISS (Steve Ouimette) | 515 | 2.42 | 16% | 0.56 | 6.50 | vacia |
| Eagles - Hotel California | Eagles | 1048 | 2.69 | 9% | 0.61 | 4.29 | vacia |
| Black Sabbath (WaveGroup) - Iron Man | Black Sabbath (WaveGroup) | 573 | 2.41 | 18% | 0.49 | 37.40 | vacia |
| Kiss - Rock And Roll All Nite | Kiss | 511 | 2.40 | 17% | 0.52 | 6.44 | vacia |
| O'Donnell_Salvatori_ Vai - Halo Theme MJOLNIR Mix | O'Donnell/Salvatori/ Vai | 624 | 2.76 | 19% | 0.48 | 32.19 | vacia |
| The Jimi Hendrix Experience - Fire | The Jimi Hendrix Experience | 464 | 2.85 | 23% | 0.53 | 5.38 | vacia |
| Kaiser Chiefs - I Predict a Riot | Kaiser Chiefs | 560 | 2.48 | 28% | 0.50 | 7.93 | vacia |
| KoRn - Word Up! | KoRn | 431 | 2.74 | 29% | 0.51 | 6.37 | vacia |
| Lost Acapulco - Olvidemos El Romance... Cojamos Ya! | Lost Acapulco | 546 | 4.41 | 39% | 0.81 | 2.77 | no respira |
| Valentin Elizalde - Vete Ya | Valentin Elizalde | 425 | 2.78 | 9% | 0.72 | 2.81 | vacia |
| Guns N' Roses - Don't Cry | Guns N' Roses | 788 | 2.82 | 8% | 0.57 | 3.69 | vacia |
| Chicos De Barrio - Mucha Lucha | Chicos De Barrio | 637 | 3.81 | 23% | 0.78 | 2.65 | no respira |
| Tame Impala - Let It Happen | Tame Impala | 1164 | 2.52 | 14% | 0.52 | 4.22 | vacia |
| Bloc Party - Helicopter | Bloc Party | 905 | 4.27 | 41% | 0.48 | 6.30 | poco vocabulario |
| Senses Fail - Can't Be Saved | Senses Fail | 730 | 3.92 | 40% | 0.73 | 2.56 | no respira |
| System of a Down - Aerials | System of a Down | 937 | 4.29 | 13% | 0.74 | 2.47 | no respira |
| Mötley Crüe (WaveGroup) - Shout At The Devil | Mötley Crüe (WaveGroup) | 518 | 2.59 | 38% | 0.53 | 3.68 | vacia |
| Foo Fighters - All My Life | Foo Fighters | 1120 | 4.30 | 34% | 0.75 | 2.44 | no respira |
| Rush (WaveGroup) - YYZ | Rush (WaveGroup) | 954 | 3.72 | 19% | 0.43 | 10.54 | poco vocabulario |
| Cream (WaveGroup) - Sunshine of Your Love | Cream (WaveGroup) | 701 | 2.71 | 7% | 0.54 | 3.38 | vacia |
| Sum 41 - In Too Deep | Sum 41 | 836 | 4.08 | 29% | 0.62 | 2.76 | no respira |
| Lynyrd Skynyrd (WaveGroup) - Free Bird | Lynyrd Skynyrd (WaveGroup) | 1982 | 3.56 | 14% | 0.47 | 6.09 | poco vocabulario |
| Green Day - American Idiot | Green Day | 689 | 4.00 | 37% | 0.65 | 2.51 | no respira |
| Loquillo Y Los Trogloditas - Cadillac Solitario (Live) | Loquillo Y Los Trogloditas | 1012 | 2.94 | 35% | 0.51 | 3.90 | vacia |
| Scorpions (Steve Ouimette) - Rock You Like A Hurricane | Scorpions (Steve Ouimette) | 843 | 3.39 | 25% | 0.45 | 6.57 | poco vocabulario |
| The Jackson 5 - I Want You Back | The Jackson 5 | 761 | 3.88 | 34% | 0.63 | 2.59 | no respira |
| Audioslave (WaveGroup) - Cochise | Audioslave (WaveGroup) | 724 | 4.00 | 7% | 0.48 | 4.38 | poco vocabulario |
| Red Hot Chili Peppers - Californication | Red Hot Chili Peppers | 869 | 2.81 | 15% | 0.53 | 3.01 | vacia |
| Scorpions - Rock You Like a Hurricane | Scorpions | 868 | 3.49 | 23% | 0.42 | 6.83 | poco vocabulario |
| My Chemical Romance - Teenagers | My Chemical Romance | 511 | 3.32 | 33% | 0.41 | 8.51 | poco vocabulario |
| Dragonforce - Through The Fire & Flames | Dragonforce | 3722 | 8.53 | 30% | 0.56 | 2.73 | no respira |
| Boston (WaveGroup) - More Than A Feeling | Boston (WaveGroup) | 726 | 2.55 | 21% | 0.50 | 3.34 | vacia |
| Metallica - That Was Just Your Life | Metallica | 2031 | 4.90 | 22% | 0.44 | 5.21 | poco vocabulario |
| David Bowie (WaveGroup) - Ziggy Stardust | David Bowie (WaveGroup) | 648 | 2.71 | 12% | 0.50 | 3.44 | vacia |
| Bryan Adams - Summer of '69 | Bryan Adams | 852 | 3.78 | 32% | 0.57 | 2.49 | no respira |
| Chingon - Malaguena Salerosa | Chingon | 812 | 3.41 | 29% | 0.47 | 4.04 | poco vocabulario |
| Alice in Chains (WaveGroup) - Them Bones | Alice in Chains (WaveGroup) | 543 | 3.50 | 26% | 0.58 | 2.30 | no respira |
| Slash - Guitar Battle vs. Slash | Slash | 886 | 4.49 | 9% | 0.48 | 3.53 | poco vocabulario |
| Junior H - Ella | Junior H | 989 | 3.90 | 22% | 0.59 | 2.23 | no respira |
| Raul di Blasio - Corazon De Niño | Raul di Blasio | 900 | 4.29 | 8% | 0.94 | 1.63 | no respira |
| Metallica - The Day That Never Comes | Metallica | 2030 | 4.30 | 15% | 0.43 | 4.63 | poco vocabulario |
| Anthrax (WaveGroup) - Madhouse | Anthrax (WaveGroup) | 1053 | 4.38 | 13% | 0.57 | 2.24 | no respira |
| Motörhead - Stay Clean | Motörhead | 614 | 3.86 | 20% | 0.55 | 2.38 | no respira |
| Gallows - Belly of a Shark | Gallows | 738 | 4.72 | 13% | 0.45 | 3.88 | poco vocabulario |
| Velvet Revolver - Slither | Velvet Revolver | 1183 | 4.82 | 15% | 0.52 | 2.62 | no respira |
| Dethklok - Thunderhorse | Dethklok | 828 | 5.94 | 31% | 0.45 | 3.84 | poco vocabulario |
| The Used - Pretty Handsome Awkward | The Used | 715 | 3.44 | 11% | 0.48 | 3.25 | poco vocabulario |
| El Tri - Triste Cancion | El Tri | 1383 | 4.14 | 15% | 0.45 | 3.63 | poco vocabulario |
| Junior H - ENTRE NOSOTROS | Junior H | 885 | 5.48 | 8% | 0.98 | 1.40 | no respira |
| Iggy Pop and the Stooges (WaveGroup) - Search and Destroy | Iggy Pop and the Stooges (WaveGroup) | 858 | 4.00 | 10% | 0.56 | 2.22 | no respira |
| Die Fantastischen Vier - Ernten Was Wir Säen | Die Fantastischen Vier | 2132 | 4.38 | 17% | 0.48 | 3.06 | poco vocabulario |
| Kikin Y Los Astros - Mi Corazon Encantado | Kikin Y Los Astros | 1072 | 3.85 | 41% | 0.83 | 1.42 | no respira |
| Steve Ouimette - We Three Kings | Steve Ouimette | 1096 | 5.57 | 17% | 0.46 | 3.28 | poco vocabulario |
| Megadeth (WaveGroup) - Hangar 18 | Megadeth (WaveGroup) | 1698 | 5.51 | 25% | 0.51 | 2.50 | no respira |
| Van Halen - Eruption | Van Halen | 804 | 8.84 | 11% | 0.25 | 23.20 | poco vocabulario |
| DragonForce - Heroes of Our Time | DragonForce | 2759 | 6.54 | 27% | 0.47 | 3.04 | poco vocabulario |
| Die Toten Hosen - Hier Kommt Alex | Die Toten Hosen | 995 | 4.38 | 26% | 0.47 | 2.88 | poco vocabulario |
| Coldplay - Yellow | Coldplay | 816 | 3.13 | 14% | 0.84 | 1.16 | no respira |
| Michael Jackson - Beat It | Michael Jackson | 815 | 3.20 | 32% | 0.40 | 4.02 | poco vocabulario |
| Linkin Park - Papercut | Linkin Park | 611 | 3.52 | 0% | 0.67 | 1.54 | no respira |
| Mathcbook Romance - Monsters | Mathcbook Romance | 1095 | 4.70 | 12% | 0.45 | 3.11 | poco vocabulario |
| DragonForce - Through the Fire and Flames | DragonForce | 3706 | 8.48 | 29% | 0.45 | 3.07 | poco vocabulario |
| Metallica - Enter Sandman | Metallica | 1270 | 3.81 | 33% | 0.51 | 2.35 | no respira |
| Junior H - Jueves 10 | Junior H | 964 | 3.43 | 15% | 0.65 | 1.53 | no respira |
| Serbia - Frio Artificial | Serbia | 774 | 3.50 | 37% | 0.35 | 4.81 | poco vocabulario |
| DragonForce - Operation Ground and Pound | DragonForce | 3200 | 6.95 | 35% | 0.50 | 2.50 | no respira |
| Linkin Park - No More Sorrow | Linkin Park | 904 | 4.14 | 6% | 0.42 | 3.48 | poco vocabulario |
| Vampire Weekend - A-Punk | Vampire Weekend | 581 | 4.51 | 9% | 0.41 | 3.72 | poco vocabulario |
| Finde - Largo Camino A Casa (Intoxicado) | Finde | 729 | 3.45 | 14% | 0.32 | 5.44 | poco vocabulario |
| Weezer - My Name Is Jonas | Weezer | 843 | 4.29 | 1% | 0.55 | 1.98 | no respira |
| Junior H - Extssy Model | Junior H | 905 | 3.85 | 26% | 0.60 | 1.69 | no respira |
| Metallica - The End of the Line | Metallica | 2408 | 5.13 | 40% | 0.28 | 6.07 | poco vocabulario |
| Queen - Stone Cold Crazy | Queen | 481 | 3.65 | 38% | 0.38 | 3.72 | poco vocabulario |
| Boys Like Girls - Thunder | Boys Like Girls | 700 | 3.17 | 41% | 0.55 | 1.85 | no respira |
| Junior H - Y LLORO | Junior H | 710 | 4.06 | 19% | 0.65 | 1.38 | no respira |
| Journey - Any Way You Want It | Journey | 728 | 3.52 | 12% | 0.37 | 3.80 | poco vocabulario |
| Natanael Cano - Madrid | Natanael Cano | 717 | 3.64 | 3% | 0.63 | 1.32 | no respira |
| Joe Satriani - Surfing With The Alien | Joe Satriani | 1088 | 4.81 | 10% | 0.34 | 4.06 | poco vocabulario |
| Blink-182 - What's My Age Again_ | Blink-182 | 634 | 4.65 | 10% | 0.51 | 2.03 | no respira |
| System of a Down - B.Y.O.B | System of a Down | 1577 | 6.20 | 35% | 0.40 | 3.27 | poco vocabulario |
| Cardenales De Nuevo León - Belleza De Cantina | Cardenales De Nuevo León | 631 | 3.60 | 11% | 0.59 | 1.48 | no respira |
| System of a Down - Toxicity | System of a Down | 967 | 4.44 | 20% | 0.49 | 2.24 | no respira |
| The Sex Pistols - Problems (Live at Brixton) | The Sex Pistols | 1206 | 4.51 | 38% | 0.58 | 1.49 | no respira |
| Blue Oyster Cult (WaveGroup) - Cities On Flame with Rock & Roll | Blue Oyster Cult (WaveGroup) | 910 | 3.78 | 6% | 0.42 | 2.86 | poco vocabulario |
| Motörhead - Motörhead | Motörhead | 912 | 5.17 | 43% | 0.50 | 2.12 | no respira |
| Leviathan - Chug Jug With You | Leviathan | 456 | 3.15 | 19% | 0.42 | 2.86 | poco vocabulario |
| Slayer - War Ensemble | Slayer | 1868 | 6.43 | 40% | 0.51 | 1.98 | no respira |
| Thrice - The Arsonist | Thrice | 989 | 4.18 | 6% | 0.50 | 2.13 | no respira |
| AFI - Carcinogen Crush | AFI | 771 | 4.59 | 21% | 0.55 | 1.57 | no respira |
| Junior H - ROCKSTAR | Junior H | 698 | 4.30 | 4% | 0.57 | 1.43 | no respira |
| Metallica - Cyanide | Metallica | 1900 | 4.83 | 31% | 0.52 | 1.81 | no respira |
| Scouts of st. Sebastian - In Love | Scouts of st. Sebastian | 910 | 4.08 | 33% | 0.21 | 4.72 | poco vocabulario |
| Disturbed - Stricken | Disturbed | 1094 | 4.56 | 41% | 0.51 | 1.82 | no respira |
| Pantera (WaveGroup) - Cowboys from Hell | Pantera (WaveGroup) | 1401 | 5.95 | 7% | 0.56 | 1.41 | no respira |
| The Fall of Troy - F.C.P.R.E.M.I.X | The Fall of Troy | 1363 | 5.78 | 20% | 0.34 | 3.45 | poco vocabulario |
| Iggy Pop - The Passenger | Iggy Pop | 1224 | 4.30 | 23% | 0.57 | 1.18 | no respira |
| Revolverheld - Generation Rock | Revolverheld | 745 | 4.97 | 40% | 0.57 | 1.18 | no respira |
| Stevie Ray Vaughn - Pride and Joy | Stevie Ray Vaughn | 984 | 4.48 | 14% | 0.51 | 1.80 | no respira |
| Tame Impala - Half Full Glass of Wine | Tame Impala | 846 | 3.72 | 27% | 0.37 | 2.95 | poco vocabulario |
| Foo Fighters - This is a call | Foo Fighters | 982 | 4.36 | 10% | 0.56 | 1.28 | no respira |
| Stevie Ray Vaughan (Steve Ouimette) - Pride & Joy | Stevie Ray Vaughan (Steve Ouimette) | 982 | 4.47 | 14% | 0.51 | 1.80 | no respira |
| Van Halen - Hot for Teacher | Van Halen | 1464 | 5.89 | 29% | 0.35 | 3.06 | poco vocabulario |
| My Chemical Romance - Dead! | My Chemical Romance | 690 | 3.60 | 27% | 0.37 | 2.88 | poco vocabulario |
| Blue Oyster Cult - Cities on Flame with Rock and Roll | Blue Oyster Cult | 914 | 3.80 | 6% | 0.37 | 2.86 | poco vocabulario |
| Cream (WaveGroup) - Crossroads | Cream (WaveGroup) | 1038 | 4.28 | 16% | 0.50 | 1.75 | no respira |
| Linkin Park - Breaking the Habit | Linkin Park | 754 | 4.50 | 37% | 0.52 | 1.22 | no respira |
| The Killers - Mr. Brightside | The Killers | 1045 | 4.90 | 5% | 0.52 | 1.05 | no respira |
| Red Hot Chili Peppers - Suck My Kiss | Red Hot Chili Peppers | 703 | 3.34 | 34% | 0.30 | 2.87 | poco vocabulario |
| Red Hot Chilli Peppers - Suck My Kiss | Red Hot Chilli Peppers | 703 | 3.34 | 34% | 0.29 | 2.87 | poco vocabulario |

## Machaconas pero te gustan

Repiten traste por encima del p75, pero salieron en un Guitar Hero o un Rock Band oficial. El punk y el pop machacan un traste por diseno: eso no es un defecto del chart. **No las borres.**

**62 canciones.**

| Cancion | Artista | Notas | n/s | Repite | Vocab. | Respira | Falla |
|---|---|---:|---:|---:|---:|---:|---|
| Prototype - The Way It Ends | Prototype | 1884 | 5.98 | 76% | 0.74 | 15.25 | machacona |
| Survivor - Eye of the Tiger | Survivor | 861 | 3.39 | 92% | 0.80 | 7.97 | machacona |
| Rise Against - Prayer of the Refugee | Rise Against | 745 | 3.80 | 78% | 0.67 | 8.55 | machacona |
| Blink-182 - Aliens Exist | Blink-182 | 912 | 4.95 | 68% | 0.74 | 6.33 | machacona |
| Europe - The Final Countdown | Europe | 1084 | 3.76 | 52% | 0.79 | 4.81 | machacona |
| Heart (WaveGroup) - Barracuda | Heart (WaveGroup) | 858 | 3.30 | 76% | 0.82 | 4.17 | machacona |
| Metallica - Orion | Metallica | 1614 | 3.70 | 50% | 0.57 | 9.41 | machacona |
| Beastie Boys - Sabotage | Beastie Boys | 731 | 4.29 | 45% | 0.57 | 8.83 | machacona |
| Metallica - Fight Fire with Fire | Metallica | 1942 | 6.96 | 67% | 0.76 | 3.75 | machacona |
| Metallica - Battery | Metallica | 1539 | 5.01 | 58% | 0.78 | 3.34 | machacona |
| Metallica - One | Metallica | 2145 | 5.07 | 45% | 0.54 | 4.95 | machacona |
| Metallica - Dyer's Eve | Metallica | 1725 | 5.52 | 53% | 0.52 | 4.94 | machacona |
| System of a Down - Chop Suey | System of a Down | 1052 | 5.31 | 63% | 0.54 | 4.20 | machacona |
| Rage Against The Machine (WaveGroup) - Killing In The Name | Rage Against The Machine (WaveGroup) | 1319 | 4.25 | 49% | 0.51 | 4.65 | machacona |
| The Hives - Tick Tick Boom | The Hives | 763 | 4.09 | 64% | 0.79 | 2.56 | machacona, no respira |
| Metallica - Creeping Death | Metallica | 1856 | 4.69 | 52% | 0.59 | 3.01 | machacona |
| AFI - Miss Murder | AFI | 811 | 4.07 | 63% | 0.50 | 4.69 | machacona |
| Motörhead - Overkill | Motörhead | 1261 | 4.66 | 44% | 0.43 | 13.41 | machacona, poco vocabulario |
| Naast - Mauvais Garcon | Naast | 780 | 4.94 | 48% | 0.50 | 4.27 | machacona |
| Slipknot - Before I Forget | Slipknot | 1091 | 4.19 | 50% | 0.80 | 2.22 | machacona, no respira |
| Naast - Mauvais Garçon | Naast | 780 | 4.94 | 48% | 0.49 | 4.27 | machacona |
| Katrina and the Waves - Walking on Sunshine | Katrina and the Waves | 945 | 4.29 | 54% | 0.72 | 2.26 | machacona, no respira |
| Metallica - Disposable Heroes | Metallica | 3156 | 6.41 | 68% | 0.56 | 2.75 | machacona, no respira |
| Diamond Head - Am I Evil_ | Diamond Head | 2041 | 4.56 | 52% | 0.41 | 6.46 | machacona, poco vocabulario |
| Carl Douglas - Kung Fu Fighting | Carl Douglas | 1072 | 5.76 | 90% | 0.35 | 20.75 | machacona, poco vocabulario |
| Green Day - Boulevard of Broken Dreams | Green Day | 859 | 3.34 | 56% | 0.56 | 2.29 | machacona, no respira |
| The Smashing Pumpkins - Cherub Rock | The Smashing Pumpkins | 1176 | 4.03 | 60% | 0.40 | 5.31 | machacona, poco vocabulario |
| Metallica - All Nightmare Long | Metallica | 3041 | 6.42 | 63% | 0.50 | 2.81 | machacona |
| Sonic Youth - Kool Thing | Sonic Youth | 1031 | 4.23 | 65% | 0.27 | 55.60 | machacona, poco vocabulario |
| Rage Against the Machine - Bulls on Parade | Rage Against the Machine | 784 | 3.44 | 46% | 0.47 | 3.14 | machacona, poco vocabulario |
| The Dead Kennedys (WaveGroup) - Holiday In Cambodia | The Dead Kennedys (WaveGroup) | 1361 | 4.89 | 55% | 0.33 | 6.66 | machacona, poco vocabulario |
| Metallica - Trapped Under Ice | Metallica | 1334 | 5.57 | 55% | 0.43 | 3.77 | machacona, poco vocabulario |
| The Who (Steve Ouimette) - The Seeker | The Who (Steve Ouimette) | 760 | 3.87 | 79% | 0.36 | 5.59 | machacona, poco vocabulario |
| No Doubt - Don't Speak | No Doubt | 917 | 3.26 | 46% | 0.61 | 1.88 | machacona, no respira |
| Metallica - The Judas Kiss | Metallica | 2367 | 4.97 | 50% | 0.45 | 3.25 | machacona, poco vocabulario |
| Blur - Song 2 | Blur | 500 | 4.51 | 92% | 0.86 | 1.13 | machacona, no respira |
| Dead Kennedys - Holiday in Cambodia | Dead Kennedys | 1320 | 4.75 | 54% | 0.33 | 5.45 | machacona, poco vocabulario |
| The Who - The Seeker | The Who | 760 | 3.87 | 78% | 0.34 | 5.32 | machacona, poco vocabulario |
| Metallica - Broken, Beat & Scarred | Metallica | 2110 | 5.53 | 58% | 0.58 | 1.75 | machacona, no respira |
| Metallica - My Apocalypse | Metallica | 1773 | 5.99 | 71% | 0.64 | 1.48 | machacona, no respira |
| Spin Doctors - Two Princes | Spin Doctors | 1064 | 4.18 | 52% | 0.32 | 4.64 | machacona, poco vocabulario |
| No Doubt - Excuse Me Mr | No Doubt | 939 | 5.17 | 45% | 0.51 | 2.17 | machacona, no respira |
| Muse - Knights of Cydonia | Muse | 1928 | 5.65 | 55% | 0.28 | 5.12 | machacona, poco vocabulario |
| Los Lobos - La Bamba | Los Lobos | 676 | 5.09 | 44% | 0.50 | 2.22 | machacona, no respira |
| Motörhead - (We Are) The Road Crew | Motörhead | 827 | 5.22 | 52% | 0.50 | 1.81 | machacona, no respira |
| Poison - Talk Dirty To Me | Poison | 796 | 3.62 | 61% | 0.49 | 1.96 | machacona, no respira |
| Trust - Antisocial | Trust | 1124 | 3.83 | 46% | 0.29 | 3.79 | machacona, poco vocabulario |
| Superbus - Radio Song | Superbus | 523 | 3.90 | 50% | 0.49 | 1.97 | machacona, no respira |
| Dick Dale (WaveGroup) - Misirlou | Dick Dale (WaveGroup) | 1221 | 7.90 | 62% | 0.44 | 2.28 | machacona, poco vocabulario, no respira |
| Dropkick Murphys - Johnny, I Hardly Knew Ya | Dropkick Murphys | 1262 | 5.45 | 47% | 0.34 | 2.93 | machacona, poco vocabulario |
| Metallica - Seek and Destroy | Metallica | 1840 | 4.49 | 46% | 0.50 | 1.82 | machacona, no respira |
| Metallica - Sad But True | Metallica | 1082 | 3.39 | 51% | 0.41 | 2.11 | machacona, poco vocabulario, no respira |
| Foo Fighters - Everlong | Foo Fighters | 1116 | 4.67 | 75% | 0.46 | 1.31 | machacona, poco vocabulario, no respira |
| Dropkick Murphys - Famous for Nothing | Dropkick Murphys | 946 | 5.84 | 55% | 0.17 | 2.46 | machacona, poco vocabulario, no respira |
| Avenged Sevenfold - Almost Easy | Avenged Sevenfold | 1113 | 4.82 | 61% | 0.39 | 1.80 | machacona, poco vocabulario, no respira |
| Iron Maiden - The Number of the Beast | Iron Maiden | 1519 | 5.77 | 56% | 0.29 | 2.13 | machacona, poco vocabulario, no respira |
| Rascal Flatts - Life Is a Highway | Rascal Flatts | 920 | 3.73 | 48% | 0.33 | 1.98 | machacona, poco vocabulario, no respira |
| We the Kings - Check Yes Juliet | We the Kings | 1005 | 4.61 | 46% | 0.38 | 1.65 | machacona, poco vocabulario, no respira |
| Elton John - Crocodile Rock | Elton John | 939 | 4.60 | 46% | 0.41 | 1.20 | machacona, poco vocabulario, no respira |
| Muse - Stockholm Syndrome | Muse | 1912 | 6.62 | 47% | 0.29 | 1.99 | machacona, poco vocabulario, no respira |
| Foo Fighters - Breakout | Foo Fighters | 781 | 3.92 | 46% | 0.35 | 1.70 | machacona, poco vocabulario, no respira |
| Muse - Assassin | Muse | 1697 | 8.16 | 62% | 0.14 | 1.24 | machacona, poco vocabulario, no respira |

## Correctas — cumplen, sin mas

Ni molestan ni ensenan nada. Se quedan.

**62 canciones.**

| Cancion | Artista | Notas | n/s | Repite | Vocab. | Respira | Falla |
|---|---|---:|---:|---:|---:|---:|---|
| Buckethead - Jordan | Buckethead | 1801 | 7.92 | 27% | 0.44 | 2.65 | poco vocabulario, no respira |
| Lacuna Coil - Closer | Lacuna Coil | 495 | 3.20 | 11% | 0.47 | 2.38 | poco vocabulario, no respira |
| Guns N' Roses - Welcome to the Jungle | Guns N' Roses | 967 | 3.75 | 22% | 0.46 | 2.45 | poco vocabulario, no respira |
| Slipknot - Himno Nacional de la Cumbia | Slipknot | 708 | 4.29 | 29% | 0.46 | 2.39 | poco vocabulario, no respira |
| DragonForce - Revolution Deathsquad | DragonForce | 3514 | 7.50 | 30% | 0.48 | 1.92 | poco vocabulario, no respira |
| The All-American Rejects - Swing, Swing | The All-American Rejects | 797 | 3.61 | 31% | 0.48 | 1.90 | poco vocabulario, no respira |
| Nirvana - Come As You Are | Nirvana | 664 | 3.20 | 19% | 0.47 | 1.97 | poco vocabulario, no respira |
| Los Rodriguez - Sin Documentos | Los Rodriguez | 985 | 3.64 | 32% | 0.41 | 2.30 | poco vocabulario, no respira |
| Jimi Hendrix (WaveGroup) - Spanish Castle Magic | Jimi Hendrix (WaveGroup) | 604 | 3.25 | 22% | 0.38 | 2.48 | poco vocabulario, no respira |
| Killswitch Engage - My Curse | Killswitch Engage | 1427 | 5.78 | 23% | 0.45 | 2.01 | poco vocabulario, no respira |
| Metallica - Fade to Black | Metallica | 1622 | 3.96 | 18% | 0.34 | 2.72 | poco vocabulario, no respira |
| Tenacious D - The Metal | Tenacious D | 897 | 5.68 | 11% | 0.46 | 1.87 | poco vocabulario, no respira |
| Metallica - Master of Puppets | Metallica | 2533 | 5.07 | 41% | 0.43 | 2.02 | poco vocabulario, no respira |
| Extremoduro - So Payaso | Extremoduro | 939 | 3.54 | 28% | 0.41 | 2.18 | poco vocabulario, no respira |
| Sum41 (WaveGroup) - Fat Lip | Sum41 (WaveGroup) | 638 | 3.60 | 29% | 0.40 | 2.26 | poco vocabulario, no respira |
| The Sex Pistols - Anarchy In The UK | The Sex Pistols | 792 | 3.70 | 32% | 0.42 | 2.12 | poco vocabulario, no respira |
| Metallica - Suicide & Redemption K.H | Metallica | 2141 | 3.66 | 22% | 0.34 | 2.56 | poco vocabulario, no respira |
| L.A. Slum Lords - Down N' Dirty | L.A. Slum Lords | 1278 | 4.02 | 24% | 0.42 | 2.09 | poco vocabulario, no respira |
| Pearl Jam - Even Flow | Pearl Jam | 1053 | 3.64 | 34% | 0.33 | 2.62 | poco vocabulario, no respira |
| Metallica - Suicide & Redemption J.H | Metallica | 2179 | 3.73 | 25% | 0.34 | 2.50 | poco vocabulario, no respira |
| Ray Parker Jr. - Ghostbusters | Ray Parker Jr. | 877 | 3.70 | 29% | 0.43 | 1.89 | poco vocabulario, no respira |
| Lions - Metal Heavy Lady | Lions | 601 | 4.27 | 27% | 0.48 | 1.45 | poco vocabulario, no respira |
| Metallica - The Unforgiven III | Metallica | 1601 | 4.07 | 15% | 0.41 | 2.10 | poco vocabulario, no respira |
| Foo Fighters (WaveGroup) - Monkey Wrench | Foo Fighters (WaveGroup) | 1037 | 4.51 | 19% | 0.47 | 1.63 | poco vocabulario, no respira |
| Black Sabbath (Steve Ouimette) - Paranoid | Black Sabbath (Steve Ouimette) | 685 | 4.17 | 5% | 0.32 | 2.58 | poco vocabulario, no respira |
| Raulin Rodriguez - Nereyda | Raulin Rodriguez | 1177 | 4.17 | 35% | 0.31 | 2.58 | poco vocabulario, no respira |
| Sex Pistols - Anarchy in the UK | Sex Pistols | 791 | 3.70 | 32% | 0.38 | 2.18 | poco vocabulario, no respira |
| Bizarrap, Nathy Peluso - Nathy Peluso_ Bzrp Music Sessions, Vol. 36 | Bizarrap, Nathy Peluso | 649 | 3.88 | 18% | 0.34 | 2.34 | poco vocabulario, no respira |
| Black Sabbath - Paranoid | Black Sabbath | 685 | 4.17 | 5% | 0.27 | 2.58 | poco vocabulario, no respira |
| The Outfield - Your Love | The Outfield | 814 | 3.92 | 43% | 0.40 | 1.98 | poco vocabulario, no respira |
| ZZ Top (Steve Ouimette) - La Grange | ZZ Top (Steve Ouimette) | 815 | 3.76 | 12% | 0.42 | 1.76 | poco vocabulario, no respira |
| Queens of the Stone Age - 3's & 7's | Queens of the Stone Age | 960 | 4.52 | 29% | 0.37 | 2.02 | poco vocabulario, no respira |
| Asspera - Hijo De Puta | Asspera | 896 | 5.17 | 42% | 0.43 | 1.52 | poco vocabulario, no respira |
| Boston - Peace Of Mind | Boston | 1057 | 3.27 | 33% | 0.46 | 1.27 | poco vocabulario, no respira |
| Foo Fighters - The Pretender | Foo Fighters | 1285 | 4.85 | 25% | 0.37 | 1.98 | poco vocabulario, no respira |
| ZZ Top - La Grange | ZZ Top | 815 | 3.76 | 12% | 0.40 | 1.76 | poco vocabulario, no respira |
| Serj Tankian - Lie Lie Lie | Serj Tankian | 686 | 3.32 | 20% | 0.36 | 1.92 | poco vocabulario, no respira |
| Fito & Fitipaldis - Por La Boca Vive El Pez | Fito & Fitipaldis | 882 | 3.43 | 30% | 0.32 | 2.17 | poco vocabulario, no respira |
| Iron Maiden (WaveGroup) - The Trooper | Iron Maiden (WaveGroup) | 1364 | 5.48 | 43% | 0.42 | 1.40 | poco vocabulario, no respira |
| Queens of the Stone Age (WaveGroup) - No One Knows | Queens of the Stone Age (WaveGroup) | 972 | 3.84 | 43% | 0.20 | 2.37 | poco vocabulario, no respira |
| Kansas (WaveGroup) - Carry On Wayward Son | Kansas (WaveGroup) | 965 | 3.25 | 9% | 0.39 | 1.68 | poco vocabulario, no respira |
| Linkin Park - Somewhere I Belong | Linkin Park | 833 | 4.16 | 18% | 0.30 | 2.14 | poco vocabulario, no respira |
| Incubus - Dig | Incubus | 1042 | 4.19 | 13% | 0.28 | 2.19 | poco vocabulario, no respira |
| Aerosmith - Same Old Song & Dance | Aerosmith | 626 | 3.62 | 18% | 0.35 | 1.83 | poco vocabulario, no respira |
| Eric Johnson - Cliffs of Dover | Eric Johnson | 1244 | 5.19 | 8% | 0.39 | 1.59 | poco vocabulario, no respira |
| Counting Crows - Accidentally in Love | Counting Crows | 628 | 3.50 | 23% | 0.37 | 1.73 | poco vocabulario, no respira |
| The Rolling Stones - Paint It Black | The Rolling Stones | 944 | 4.22 | 20% | 0.38 | 1.56 | poco vocabulario, no respira |
| The Strokes - Reptilia | The Strokes | 829 | 4.04 | 24% | 0.29 | 2.07 | poco vocabulario, no respira |
| Def Leppard - Nine Lives | Def Leppard | 709 | 3.34 | 37% | 0.39 | 1.46 | poco vocabulario, no respira |
| Metallica - Fuel | Metallica | 1241 | 4.76 | 27% | 0.23 | 2.15 | poco vocabulario, no respira |
| Aerosmith - Same Old Song and Dance | Aerosmith | 626 | 3.62 | 18% | 0.33 | 1.83 | poco vocabulario, no respira |
| My Chemical Romance - Famous Last Words | My Chemical Romance | 1234 | 4.16 | 35% | 0.32 | 1.84 | poco vocabulario, no respira |
| Priestess - Lay Down | Priestess | 766 | 4.22 | 27% | 0.14 | 2.14 | poco vocabulario, no respira |
| Radio Futura - Escuela de Calor | Radio Futura | 949 | 4.66 | 39% | 0.22 | 2.11 | poco vocabulario, no respira |
| In Flames - Take This Life | In Flames | 1608 | 7.56 | 36% | 0.40 | 1.15 | poco vocabulario, no respira |
| Muse - Super Massive Black Hole | Muse | 681 | 3.29 | 35% | 0.24 | 1.89 | poco vocabulario, no respira |
| Van Halen - Ain't Talkin' 'Bout Love | Van Halen | 745 | 3.33 | 25% | 0.24 | 1.83 | poco vocabulario, no respira |
| Muse - Exo-Politics | Muse | 772 | 3.40 | 31% | 0.31 | 1.49 | poco vocabulario, no respira |
| Miguel Bose - Nena (Ft. Paulina Rubio) | Miguel Bose | 943 | 3.87 | 0% | 0.27 | 1.65 | poco vocabulario, no respira |
| El de la guitarra - A lo lejos me veran | El de la guitarra | 547 | 3.70 | 9% | 0.26 | 1.35 | poco vocabulario, no respira |
| Dropkick Murphys - (F)lannigan's Ball | Dropkick Murphys | 1270 | 5.88 | 37% | 0.21 | 1.26 | poco vocabulario, no respira |
| Brunich - Electro Guitar Cyber Club | Brunich | 536 | 3.36 | 25% | 0.24 | 1.07 | poco vocabulario, no respira |

## Machaconas y prescindibles

Repiten traste por encima del p75 **y** no salieron en ningun juego oficial. Estas son las candidatas reales a borrar.

**16 canciones.**

| Cancion | Artista | Notas | n/s | Repite | Vocab. | Respira | Falla |
|---|---|---:|---:|---:|---:|---:|---|
| Motel - Y Te Vas | Motel | 786 | 3.64 | 52% | 0.68 | 4.08 | machacona |
| Hombres G - Venecia | Hombres G | 643 | 3.36 | 46% | 0.56 | 4.27 | machacona |
| Mago de Oz - La Rosa de los Vientos | Mago de Oz | 1558 | 4.14 | 48% | 0.66 | 3.17 | machacona |
| Molotov - Gimme Tha Power | Molotov | 1242 | 5.06 | 49% | 0.62 | 3.47 | machacona |
| Timbiriche - Corro, Vuelo, Me Acelero | Timbiriche | 878 | 3.80 | 57% | 0.44 | 5.70 | machacona, poco vocabulario |
| Ska-P - Welcome To Hell | Ska-P | 765 | 3.14 | 48% | 0.44 | 4.21 | machacona, poco vocabulario |
| Cuca - El Son Del Dolor | Cuca | 857 | 3.66 | 47% | 0.38 | 5.87 | machacona, poco vocabulario |
| Enrique Guzman & Teen Tops - La Plaga | Enrique Guzman & Teen Tops | 652 | 5.22 | 74% | 0.73 | 1.80 | machacona, no respira |
| Christian Nodal & Angela Aguilar - Dime Como Quieres | Christian Nodal & Angela Aguilar | 666 | 4.11 | 82% | 0.70 | 1.22 | machacona, no respira |
| Caballo Dorado - El Payaso del Rodeo | Caballo Dorado | 1779 | 7.15 | 45% | 0.25 | 3.28 | machacona, poco vocabulario |
| Mago de Oz - Fiesta Pagana | Mago de Oz | 1037 | 3.76 | 58% | 0.28 | 2.82 | machacona, poco vocabulario |
| Los Fabulosos Cadillacs - Contrabando De Amor | Los Fabulosos Cadillacs | 615 | 3.19 | 66% | 0.13 | 2.90 | machacona, poco vocabulario |
| Menudo - Subete A Mi Moto | Menudo | 821 | 3.95 | 70% | 0.34 | 1.71 | machacona, poco vocabulario, no respira |
| Mago de Oz - Molinos de Viento | Mago de Oz | 1026 | 4.14 | 49% | 0.30 | 1.84 | machacona, poco vocabulario, no respira |
| Aaron Montalvo - Mi corazón encantado (GT) | Aaron Montalvo | 790 | 3.87 | 68% | 0.32 | 1.65 | machacona, poco vocabulario, no respira |
| Siddhartha - Unicos | Siddhartha | 889 | 3.74 | 81% | 0.08 | 1.24 | machacona, poco vocabulario, no respira |

## Vacias — casi no tocas

Por debajo del p25 de notas por segundo y fallando algo mas. Si la cancion te gusta, busca otro chart en Chorus en vez de borrarla.

**61 canciones.**

| Cancion | Artista | Notas | n/s | Repite | Vocab. | Respira | Falla |
|---|---|---:|---:|---:|---:|---:|---|
| Julieta Venegas - Eres Para Mi | Julieta Venegas | 521 | 2.76 | 96% | 0.99 | 32.40 | machacona, vacia |
| Julieta Venegas - El Presente (MTV Unplugged) | Julieta Venegas | 643 | 3.06 | 78% | 0.84 | 5.26 | machacona, vacia |
| Linkin Park - Given Up | Linkin Park | 504 | 2.76 | 77% | 0.67 | 7.81 | machacona, vacia |
| Shakira - La Tortura (Ft. Alejandro Sanz) | Shakira | 401 | 1.90 | 47% | 0.58 | 26.82 | machacona, vacia |
| Muse - Can't Take My Eyes Of You | Muse | 559 | 2.75 | 46% | 0.63 | 8.37 | machacona, vacia |
| The Police - Every Little Thing She Does Is Magic | The Police | 651 | 2.50 | 28% | 0.79 | 2.79 | vacia, no respira |
| Nightwish - Ghost Love Score | Nightwish | 1538 | 2.60 | 46% | 0.51 | 5.70 | machacona, vacia |
| The Killers - When You Were Young | The Killers | 564 | 2.69 | 16% | 0.47 | 14.79 | vacia, poco vocabulario |
| Bon Jovi - You Give Love a Bad Name | Bon Jovi | 533 | 2.66 | 18% | 0.46 | 7.58 | vacia, poco vocabulario |
| Linkin Park - Shadow of the Day | Linkin Park | 766 | 3.05 | 30% | 0.90 | 2.20 | vacia, no respira |
| Linkin Park - What I've Done | Linkin Park | 476 | 2.45 | 13% | 0.41 | 39.60 | vacia, poco vocabulario |
| Los Tigres Del Norte - Golpes En El Corazon (MTV Unplugged - Con Paulina Rubio) | Los Tigres Del Norte | 664 | 2.77 | 60% | 0.81 | 2.18 | machacona, vacia, no respira |
| Foghat (WaveGroup) - Slow Ride | Foghat (WaveGroup) | 551 | 2.26 | 22% | 0.69 | 2.35 | vacia, no respira |
| Ed Maverick - Fuentes de Ortiz | Ed Maverick | 457 | 2.32 | 21% | 0.65 | 2.42 | vacia, no respira |
| Backyard Babies - Minus Celsius | Backyard Babies | 615 | 2.88 | 57% | 0.49 | 4.01 | machacona, vacia |
| Primus - John the Fisherman | Primus | 420 | 2.20 | 20% | 0.65 | 2.33 | vacia, no respira |
| Nirvana - All Apologies | Nirvana | 652 | 2.92 | 28% | 0.42 | 6.64 | vacia, poco vocabulario |
| Julio Jaramillo - Cuando llora mi guitarra | Julio Jaramillo | 543 | 2.91 | 20% | 0.55 | 2.79 | vacia, no respira |
| M-Clan - Carolina | M-Clan | 637 | 2.54 | 4% | 0.59 | 2.41 | vacia, no respira |
| Jaguares - Fin | Jaguares | 471 | 1.83 | 9% | 0.63 | 2.23 | vacia, no respira |
| Aerosmith - Dream On | Aerosmith | 622 | 2.44 | 47% | 0.81 | 1.89 | machacona, vacia, no respira |
| The Stone Roses (WaveGroup) - She Bangs The Drums | The Stone Roses (WaveGroup) | 684 | 3.12 | 13% | 0.46 | 3.92 | vacia, poco vocabulario |
| Guns n' Roses (WaveGroup) - Sweet Child O' Mine | Guns n' Roses (WaveGroup) | 998 | 2.85 | 10% | 0.46 | 3.87 | vacia, poco vocabulario |
| Megadeth (WaveGroup) - Symphony Of Destruction | Megadeth (WaveGroup) | 681 | 2.99 | 15% | 0.47 | 3.63 | vacia, poco vocabulario |
| Hombres G - Devuelveme A Mi Chica | Hombres G | 541 | 2.86 | 32% | 0.34 | 10.18 | vacia, poco vocabulario |
| Green Day - 21 Guns | Green Day | 675 | 2.17 | 20% | 0.55 | 2.48 | vacia, no respira |
| El Cuarteto De Nos - Vida Ingrata | El Cuarteto De Nos | 643 | 2.77 | 27% | 0.32 | 15.35 | vacia, poco vocabulario |
| Juanes - Nada Valgo Sin Tu Amor | Juanes | 545 | 2.91 | 3% | 0.47 | 3.49 | vacia, poco vocabulario |
| RBD - Rebelde | RBD | 571 | 2.76 | 18% | 0.51 | 2.73 | vacia, no respira |
| No Doubt - Sunday Morning | No Doubt | 623 | 2.44 | 19% | 0.43 | 3.71 | vacia, poco vocabulario |
| Eslabon Armado - Jugaste y Sufrí (ft. DannyLux) | Eslabon Armado | 815 | 3.02 | 15% | 0.56 | 2.12 | vacia, no respira |
| Heroes del Silencio - Avalancha | Heroes del Silencio | 968 | 2.76 | 26% | 0.38 | 4.68 | vacia, poco vocabulario |
| Kaiser Chiefs - Ruby | Kaiser Chiefs | 495 | 2.57 | 31% | 0.46 | 3.18 | vacia, poco vocabulario |
| Red Hot Chili Peppers - Otherside | Red Hot Chili Peppers | 506 | 2.05 | 41% | 0.41 | 3.82 | vacia, poco vocabulario |
| Coldplay - God Put A Smile Upon Your Face | Coldplay | 828 | 2.89 | 67% | 0.51 | 2.35 | machacona, vacia, no respira |
| Green Day - Wake Me Up When September Ends | Green Day | 828 | 2.97 | 23% | 0.44 | 3.27 | vacia, poco vocabulario |
| Linkin Park - New Divide | Linkin Park | 716 | 2.76 | 76% | 0.09 | 18.91 | machacona, vacia, poco vocabulario |
| Pat Benatar - Hit Me With Your Best Shot | Pat Benatar | 491 | 2.94 | 28% | 0.48 | 2.79 | vacia, poco vocabulario, no respira |
| Gustavo Cerati - La Excepcion | Gustavo Cerati | 772 | 3.11 | 56% | 0.29 | 6.30 | machacona, vacia, poco vocabulario |
| Tame Impala - Elephant | Tame Impala | 642 | 3.09 | 4% | 0.50 | 2.21 | vacia, no respira |
| David Bowie - Let's Dance | David Bowie | 496 | 1.72 | 21% | 0.38 | 3.53 | vacia, poco vocabulario |
| Social Distortion - Story of My Life | Social Distortion | 936 | 2.75 | 32% | 0.43 | 2.57 | vacia, poco vocabulario, no respira |
| Odisseo - Los Imanes | Odisseo | 536 | 2.50 | 32% | 0.46 | 2.29 | vacia, poco vocabulario, no respira |
| The Cranberries - Zombie | The Cranberries | 593 | 1.98 | 8% | 0.39 | 2.78 | vacia, poco vocabulario, no respira |
| ZOE - Asteroide | ZOE | 548 | 2.88 | 20% | 0.32 | 3.32 | vacia, poco vocabulario |
| Velvet Revolver - Messages | Velvet Revolver | 631 | 2.28 | 10% | 0.52 | 1.52 | vacia, no respira |
| Alice Cooper - School's Out | Alice Cooper | 471 | 2.50 | 34% | 0.36 | 2.77 | vacia, poco vocabulario, no respira |
| Santana - Black Magic Woman | Santana | 796 | 2.56 | 25% | 0.35 | 2.63 | vacia, poco vocabulario, no respira |
| Luis Miguel - Ahora Te Puedes Marchar | Luis Miguel | 488 | 2.76 | 20% | 0.26 | 3.16 | vacia, poco vocabulario |
| Cartel De Santa - Todas Mueren Por Mi | Cartel De Santa | 454 | 2.08 | 26% | 0.05 | 3.51 | vacia, poco vocabulario |
| Bon Jovi - Livin' on a Prayer | Bon Jovi | 731 | 2.78 | 15% | 0.34 | 2.51 | vacia, poco vocabulario, no respira |
| Buckethead - The Left Panel | Buckethead | 1785 | 1.55 | 27% | 0.41 | 2.00 | vacia, poco vocabulario, no respira |
| Kasabian - Shoot the Runner | Kasabian | 555 | 2.75 | 26% | 0.40 | 2.03 | vacia, poco vocabulario, no respira |
| ZZ Top (WaveGroup) - Sharp Dressed Man | ZZ Top (WaveGroup) | 759 | 2.78 | 17% | 0.24 | 2.42 | vacia, poco vocabulario, no respira |
| Nirvana (WaveGroup) - Heart-Shaped Box | Nirvana (WaveGroup) | 850 | 2.87 | 19% | 0.37 | 1.87 | vacia, poco vocabulario, no respira |
| Tame Impala - Mind Mischief | Tame Impala | 635 | 2.40 | 38% | 0.41 | 1.62 | vacia, poco vocabulario, no respira |
| RBD - Salvame | RBD | 545 | 2.50 | 5% | 0.44 | 1.02 | vacia, poco vocabulario, no respira |
| Mikel Erentxun - A Un Minuto De Ti | Mikel Erentxun | 594 | 2.62 | 24% | 0.36 | 1.41 | vacia, poco vocabulario, no respira |
| Rubius - Minero | Rubius | 626 | 2.96 | 31% | 0.27 | 1.67 | vacia, poco vocabulario, no respira |
| Arctic Monkeys - Teddy Picker | Arctic Monkeys | 472 | 3.00 | 32% | 0.29 | 1.52 | vacia, poco vocabulario, no respira |
| Jhay Cortez - No Me Conoce - Remix (feat. J Balvin, Bad Bunny) | Jhay Cortez | 566 | 1.94 | 8% | 0.20 | 1.27 | vacia, poco vocabulario, no respira |
