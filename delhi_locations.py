
DELHI_LOCATIONS = {
    'kashmere gate, delhi': (28.6668141, 77.2290549),
    'malviya nagar, delhi': (28.5339201, 77.2124474),
    'delhi airport': (28.5610952, 77.0853142),
    'red fort, delhi': (28.656081, 77.2407959),
    'india gate, new delhi': (28.6129332, 77.2294928),
    'hauz khas, delhi': (28.5498087, 77.2077638),
    'connaught place, new delhi': (28.6314022, 77.2193791),
    'karol bagh, delhi': (28.6529982, 77.1890227),
    'lajpat nagar, delhi': (28.5660924, 77.2432851),
    'dwarka, new delhi': (28.574272, 77.0653316),
    'rajouri garden, delhi': (28.6511896, 77.1242597),
    'chandni chowk, delhi': (28.6559834, 77.2321937),
    'greater kailash, new delhi': (28.5555167, 77.2634965),
    'rohini, delhi': (28.7162092, 77.1170743),
    'saket, new delhi': (28.5234897, 77.209631),
    'nehru place, delhi': (28.5492574, 77.2529526),
    'sarojini nagar market': (28.5769159, 77.1962566),
    'kamla nagar market': (28.6786683, 77.2072566),
    'defence colony, delhi': (28.5713575, 77.2330402),
    'green park, delhi': (28.5564421, 77.2038699),
    'okhla industrial area, delhi': (28.5475409, 77.2828271),
    'nizamuddin, delhi': (28.5909417, 77.2423341),
    'chanakyapuri, delhi': (28.5946775, 77.1885212),
    'lutyens, delhi': (28.6025053, 77.2279312),
    'akshardham temple, delhi': (28.6125167, 77.2773184),
    'lotus temple, delhi': (28.5533586, 77.2586006),
    'qutub minar, delhi': (28.524413, 77.1854501),
    'national museum, new delhi': (28.6119151, 77.2196391),
    "humayun's tomb, delhi": (28.5932856, 77.2506468),
    'mehrauli, delhi': (28.5218262, 77.1783232),
    'jawaharlal nehru university, new delhi': (28.5401668, 77.1645601),
    'delhi university': (28.7508153, 77.1162765),
}

def get_coordinates(place_name):
    """Returns the coordinates for a given place name."""
    return DELHI_LOCATIONS.get(place_name.lower())
