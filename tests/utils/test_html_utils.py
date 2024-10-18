from rudi_node_write.utils.html_utils import textify_html


def test_textify_html():
    html_str = (
        '<p>Etat du trafic en temps réel. Données fournies à Rennes Métropole par la société Autoroutes Trafic. </p><p>Ces données ont un "délai" de 3 minutes, il est donc normal qu\'à 15h30, la donnée la plus récente indique 15h27.</p><p>Ce jeu de données a été lié à une couche spécifique du RVA pour faciliter la réutilisation:</p><p><a href="https://data.rennesmetropole.fr/explore/dataset/troncons-de-voies-support-pour-les-donnees-de-trafic-routier-temps-reel/information/" target="_blank">https://data.rennesmetropole.fr/explore/dataset/troncons-de-voies-support-pour-les-donnees-de-trafic-routier-temps-reel/information/</a></p><p>Si vous le souhaitez, vous pouvez directement accéder à l\'API DKAN et faire la jointure vous même.</p><p><a href="http://dkan.autoroutes-trafic.fr/?q=dataset/donn%C3%A9es-trafic-rennes-m%C3%A9tropole">http://dkan.autoroutes-trafic.fr/?q=dataset/donn%C...</a></p><p>Si vous vous retrouvez dans le cas d\'un usage spécifique et avez besoin d\'un quota d\'API supplémentaire, contactez nous via le formulaire ou le forum. </p><p>Description des champs.</p>'
        '<ul> <li>datetime : l’horodate de l’information au format ISO 8601 (<a href="https://www.iso.org/iso-8601-date-and-time-format.html">https://www.iso.org/iso-8601-date-and-time-format.html</a>)</li><li>predefinedLocationRerefence : l’identifiant du tronçon Rennes Métropole auquel l’information est rattachée. L’identifiant peut être suffixé par « _D » et « _G » dans le cas de tronçon à double sens de circulation. Le sens de numérisation du tronçon est alors le sens « D », le sens inverse le sens « G ».</li><li>averageVehicleSpeed : la vitesse moyenne des véhicules circulant sur le tronçon, en kilomètre par heure.</li><li>travelTime : le temps de parcours du tronçon, en secondes.</li><li>travelTimeReliability : la fiabilité du temps de parcours fournis, en pourcentage de 0% à 100%.</li><li>trafficStatus : l’état du trafic sur le tronçon, les valeurs possibles sont : <ul> <li>unknown : état inconnu</li><li>freeFlow : fluide</li><li>heavy : chargé</li><li>congested : congestionné</li><li>impossible : circulation impossible</li></ul></li></ul>'
    )
    assert textify_html(html_str).find("</") == -1
