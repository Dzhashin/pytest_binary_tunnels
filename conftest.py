import pytest
import yaml
from fabric import Connection

@pytest.fixture(scope="session")
def config():
    with open("test_matrix.yaml", "r") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="session")
def tunnel_mgr(config):
    env = config['env']
    class Manager:
        def __init__(self):
            self.trans = Connection(host=env['transmitter_ip'], user=env['user'])
            self.rec = Connection(host=env['receiver_ip'], user=env['user'])
        
        def run_trans(self, cmd, sudo=False):
            # Using sudo if requested, otherwise run normal command
            # hide=True keeps the pytest output clean unless the test fails
            return self.trans.sudo(cmd, hide=True) if sudo else self.trans.run(cmd, hide=True)
        
        def run_rec(self, cmd, sudo=False):
            return self.rec.sudo(cmd, hide=True) if sudo else self.rec.run(cmd, hide=True)

    return Manager()
