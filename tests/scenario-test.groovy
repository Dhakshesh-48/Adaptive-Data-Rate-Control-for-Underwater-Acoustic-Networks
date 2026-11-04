def loader = new GroovyClassLoader(this.class.classLoader)
def clazz = loader.parseClass(new File('classes/ScenarioChannelModel.groovy'))
assert clazz.newInstance('good').probabilitiesAt(0) == [detection:0.995f, decoding:0.995f]
assert clazz.newInstance('moderate').probabilitiesAt(0) == [detection:0.96f, decoding:0.94f]
assert clazz.newInstance('poor').probabilitiesAt(0) == [detection:0.85f, decoding:0.75f]
def step = clazz.newInstance('step')
assert step.probabilitiesAt(119999).decoding == 0.995f
assert step.probabilitiesAt(120000).decoding == 0.75f
assert step.probabilitiesAt(240000).decoding == 0.995f
println 'SCENARIO_TEST_PASS'
