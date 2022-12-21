# PR5_AlgoritmoMaekawa
Entrega practica 5 de la asignatura de Arquitecturas avanzadas
Práctica 5: Algoritmo de Maekawa.
Implementar el algoritmo de maekawa desde el esqueleto facilitado.

Lógica implementada en el algoritmo de Maekawa.
Diferenciar Sección crítica, preprotocolo y postprotocolo.

Con el código facilitado solo debo de modificar el mutex e implementar el acceso a la sección crítica del cliente, conceder o denegar acceso y liberar la región. 
El algoritmo a priori funciona de la siguiente manera. Se posee una serie de nodos que pertenecen a subgrupos. Cada subgrupo debe mandar un mensaje de aprobación al nodo de ese mismo subgrupo que quiera entrar en la región crítica. En caso de no recibir el mensaje se esperará, pues se asumirá que hay otro nodo en región crítica.

He jugado a los legos con el algoritmo de maekawa facilitado en el readme de la práctica. 
Inicialmente parecía sencillo gestionar el mútex y las simulaciones de una región crítica pero me ha resultado imposible con la estructura dada. No era capaz de hacerlo funcionar. 
He optado por interpretar el código de maekawa del enlace y me he dado cuenta que la parte facilitada era muy parecida a la del ejemplo, pero sin los métodos implementados. 
Es por ello que he tratado de adaptar el algoritmo faltante con el código de github.
Concretamente, y dado que se especificaba en el propio código de la práctica, se ha trabajado sobre el node.py en la parte del state, junto a todos los métodos necesarios para su funcionamiento. Y en el nodeServer en el apartado de process_message, junto a todos los métodos necesarios para procesar el mensaje especificados. 
Se han hecho una serie de ajustes, y los prints no son los más perfectos, pero no saltan errores.
He tenido además que añadir el método update del código en el apartado de nodeSend para que este hiciera el intento de entrar, gestionar, y salir de la región crítica. 

https://github.com/yvetterowe/Maekawa-Mutex
