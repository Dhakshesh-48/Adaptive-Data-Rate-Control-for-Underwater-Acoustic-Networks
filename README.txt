UnetStack Community Edition
===========================

Requirements
------------

Mac OS X / Linux / Windows
Java 8 installed
Chrome 61+ / Firefox 60+ / Safari 10.1+

Getting started
---------------

To start a simulated 2-node underwater network, open a terminal window in the
unet folder (where this README.txt is) and try:

  bin/unet samples/2-node-network.groovy

  2-node network
  --------------

  Node A: tcp://localhost:1101, http://localhost:8081/
  Node B: tcp://localhost:1102, http://localhost:8082/

Open the two http URLs shown above in a web browser to get a command shell on
each of the simulated nodes. To explore what you can do from the shell, type
'help' in it. This is a realtime simulation, so it keeps running until you
stop it with Ctrl-C.

Simulations can also run faster than realtime in discrete-event mode. To try
a pure ALOHA throughput simulation, run:

  bin/unet samples/aloha.groovy

If everything goes well, you should see an output similar to:

  Pure ALOHA simulation
  =====================

  TX Count        RX Count        Offered Load    Throughput
  --------        --------        ------------    ----------
     598             507            0.097           0.080
    1176             860            0.195           0.137
    1705            1010            0.289           0.160
    2286            1090            0.397           0.173
    2830            1179            0.504           0.187
    3227            1182            0.584           0.188
    3768            1149            0.704           0.182
    4232            1000            0.814           0.159
    4564             917            0.885           0.146
    5080             935            1.004           0.148
    5464             775            1.098           0.123
    5832             677            1.209           0.107
    6218             628            1.287           0.100
    6644             538            1.404           0.085
    7022             462            1.507           0.073

If not, visit the support forum at http://www.unetstack.net/ to seek help on
resolving the problem.

To get going with developing your own networks, protocol and simulations, read
the Unet handbook at http://www.unetstack.net/handbook/

Bundled dependencies
--------------------

The UnetStack community edition depends on the several open-source software libraries that
are bundled together in this package in binary form:

Groovy - Apache License v2 (http://www.apache.org/licenses/LICENSE-2.0.html)
Apache Commons - Apache License v2 (http://www.apache.org/licenses/LICENSE-2.0.html)
fjåge - BSD License (https://raw.github.com/org-arl/fjage/master/LICENSE.txt)
jline - BSD License (https://raw.github.com/jline/jline3/master/LICENSE.txt)
GSON - Apache License v2 (http://www.apache.org/licenses/LICENSE-2.0.html)
OpenRQ - Apache License v2 (http://www.apache.org/licenses/LICENSE-2.0.html)
Objenesis - Apache License v2 (http://www.apache.org/licenses/LICENSE-2.0.html)
cloning - Apache License v2 (http://www.apache.org/licenses/LICENSE-2.0.html)
toml4j - MIT License (https://github.com/mwanji/toml4j/blob/master/LICENSE)
jetty (incl. websocket) - Eclipse Public License - v 1.0 (https://www.eclipse.org/org/documents/epl-v10.php)
javax.servlet-api - CDDL + GPLv2 with classpath exception (https://javaee.github.io/glassfish/LICENSE)
jSerialComm - Apache License v2 (http://www.apache.org/licenses/LICENSE-2.0.html)
error_prone_annotations - Apache License v2 (http://www.apache.org/licenses/LICENSE-2.0.html)
