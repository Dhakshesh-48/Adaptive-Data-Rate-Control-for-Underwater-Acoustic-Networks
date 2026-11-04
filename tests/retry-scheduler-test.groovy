def loader = new GroovyClassLoader(this.class.classLoader)
def schedulerClass = loader.parseClass(new File('classes/RetryScheduler.groovy'))

def scheduler = schedulerClass.newInstance(3, 2)

// Proposed mode samples exactly the final original for each receiver in a ten-message window.
assert (1..8).every { !scheduler.ackRequested('proposed', it, 10, 1) }
assert scheduler.ackRequested('proposed', 9, 10, 1)
assert scheduler.ackRequested('proposed', 10, 10, 1)
assert (1..10).every { scheduler.ackRequested('fixed', it, 10, 1) }
assert scheduler.ackRequested('proposed', 1, 10, 2)

// A controller decision cannot change pacing inside an already-started window.
def pacingScheduler = schedulerClass.newInstance(3, 2)
assert pacingScheduler.intervalForOpportunity(3000) == 3000
pacingScheduler.noteOriginal(1, 10, 3000)
assert pacingScheduler.intervalForOpportunity(2250) == 3000
(2..9).each { pacingScheduler.noteOriginal(it, 10, 3000) }
assert pacingScheduler.intervalForOpportunity(2250) == 3000
pacingScheduler.noteOriginal(10, 10, 3000)
assert pacingScheduler.intervalForOpportunity(2250) == 2250

// Missing IDs are sorted, capped per original window, and never queued twice.
assert scheduler.enqueue(4, 3, [5,3,4]) == [3,4]
assert scheduler.enqueue(4, 3, [3,4,5]).isEmpty()
assert scheduler.queuedCount() == 2

// One retry opportunity follows every three new originals and cannot starve indefinitely.
scheduler.noteOriginal(); scheduler.noteOriginal()
assert scheduler.takeRetry(true) == null
scheduler.noteOriginal()
assert scheduler.takeRetry(false) == null
assert scheduler.queuedCount() == 2
assert scheduler.takeRetry(true) == [windowId:4, destination:3, seq:3, attempt:2]
assert scheduler.queuedCount() == 1
scheduler.noteOriginal(); scheduler.noteOriginal(); scheduler.noteOriginal()
assert scheduler.takeRetry(true) == [windowId:4, destination:3, seq:4, attempt:2]
assert scheduler.queuedCount() == 0

// A sequence already selected for retry cannot re-enter the queue.
assert scheduler.enqueue(5, 2, [3,6]) == [6]
assert scheduler.enqueue(5, 2, [6]).isEmpty()

boolean invalid = false
try { schedulerClass.newInstance(0, 2) } catch (IllegalArgumentException ignored) { invalid = true }
assert invalid
println 'RETRY_SCHEDULER_TEST_PASS'
