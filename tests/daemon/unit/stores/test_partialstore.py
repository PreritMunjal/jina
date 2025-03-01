from pathlib import Path

import pytest

from daemon.models import PeaModel, FlowModel
from daemon.stores.partial import PartialPeaStore, PartialFlowStore
from jina import helper, Flow, __default_host__
from jina.helper import ArgNamespace
from jina.parsers import set_pea_parser
from jina.parsers.flow import set_flow_parser

cur_dir = Path(__file__).parent


@pytest.fixture()
def partial_pea_store():
    partial_pea_store = PartialPeaStore()
    yield partial_pea_store
    partial_pea_store.delete()


@pytest.fixture()
def partial_flow_store():
    partial_flow_store = PartialFlowStore()
    yield partial_flow_store
    partial_flow_store.delete()


def test_peastore_add(partial_pea_store):
    partial_store_item = partial_pea_store.add(
        args=ArgNamespace.kwargs2namespace(PeaModel().dict(), set_pea_parser())
    )
    assert partial_store_item
    assert partial_pea_store.object
    assert partial_store_item.arguments['runtime_cls'] == 'ZEDRuntime'
    assert partial_store_item.arguments['host_in'] == __default_host__
    assert partial_store_item.arguments['host_out'] == __default_host__


@pytest.mark.timeout(5)
def test_partial_peastore_delete(monkeypatch, mocker):
    close_mock = mocker.Mock()
    partial_store = PartialPeaStore()

    partial_store.object = close_mock
    partial_store.delete()
    close_mock.close.assert_called()


def test_flowstore_add(monkeypatch, partial_flow_store):
    flow_model = FlowModel()
    flow_model.uses = f'{cur_dir}/flow.yml'
    args = ArgNamespace.kwargs2namespace(flow_model.dict(), set_flow_parser())
    partial_store_item = partial_flow_store.add(args)

    assert partial_store_item
    assert isinstance(partial_flow_store.object, Flow)
    assert 'executor1' in partial_store_item.yaml_source
    assert partial_flow_store.object.port_expose == 12345


def test_flowstore_rolling_update(partial_flow_store, mocker):
    flow_model = FlowModel()
    flow_model.uses = f'{cur_dir}/flow.yml'
    args = ArgNamespace.kwargs2namespace(flow_model.dict(), set_flow_parser())

    partial_flow_store.add(args)

    rolling_update_mock = mocker.Mock()
    partial_flow_store.object.rolling_update = rolling_update_mock

    partial_flow_store.rolling_update(pod_name='executor1', uses_with={})
    rolling_update_mock.assert_called()


def test_flowstore_scale(partial_flow_store, mocker):
    flow_model = FlowModel()
    flow_model.uses = f'{cur_dir}/flow.yml'
    args = ArgNamespace.kwargs2namespace(flow_model.dict(), set_flow_parser())

    partial_flow_store.add(args)

    scale_mock = mocker.Mock()
    partial_flow_store.object.scale = scale_mock

    partial_flow_store.scale(pod_name='executor1', replicas=2)
    scale_mock.assert_called()
