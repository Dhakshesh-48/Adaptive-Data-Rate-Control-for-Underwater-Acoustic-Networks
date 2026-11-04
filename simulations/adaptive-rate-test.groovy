import org.arl.fjage.*

println '''
Adaptive Data Rate Control — 3 Node Network

Node A: sender
Node B: receiver
Node C: receiver

Node A sends packets alternately to B and C.
Open http://localhost:8081/ for Node A
Open http://localhost:8082/ for Node B
Open http://localhost:8083/ for Node C
'''

platform = RealTimePlatform

simulate {
  node 'A',
    address: 1,
    location: [0.km, 0.km, -15.m],
    web: 8081,
    api: 1101,
    stack: "$home/etc/setup"

  node 'B',
    address: 2,
    location: [1.km, 0.km, -15.m],
    web: 8082,
    api: 1102,
    stack: "$home/etc/setup"

  node 'C',
    address: 3,
    location: [2.km, 0.km, -15.m],
    web: 8083,
    api: 1103,
    stack: "$home/etc/setup"
}
