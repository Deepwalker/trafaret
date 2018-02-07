from pyannotate_runtime import collect_types


collect_types.init_types_collection()


def pytest_runtest_call(*a):
    collect_types.resume()

def pytest_runtest_teardown(*a):
    collect_types.pause()

def pytest_unconfigure(*a):
    collect_types.dump_stats('/Users/mkrivushin/w/trafaret/annotations.json')
