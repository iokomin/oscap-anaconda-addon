#
# Copyright (C) 2013  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Vratislav Podzimek <vpodzime@redhat.com>
#

"""Module with unit tests for the common.py module"""

import os
import mock

import pytest

from org_fedora_oscap import common


@pytest.fixture()
def mock_subprocess():
    mock_subprocess = mock.Mock()
    mock_subprocess.Popen = mock.Mock()
    mock_popen = mock.Mock()
    mock_communicate = mock.Mock()

    mock_communicate.return_value = ("", "")

    mock_popen.communicate = mock_communicate
    mock_popen.returncode = 0

    mock_subprocess.Popen.return_value = mock_popen
    mock_subprocess.PIPE = mock.Mock()

    return mock_subprocess


def mock_run_remediate(mock_subprocess, monkeypatch):
    mock_utils = mock.Mock()
    mock_utils.ensure_dir_exists = mock.Mock()

    common_module_symbols = common.__dict__

    monkeypatch.setitem(common_module_symbols, "subprocess", mock_subprocess)
    monkeypatch.setitem(common_module_symbols, "utils", mock_utils)


def _run_oscap(mock_subprocess, additional_args):
    expected_args = [
        "oscap", "xccdf", "eval", "--remediate",
        "--results=%s" % common.RESULTS_PATH,
        "--report=%s" % common.REPORT_PATH,
        "--profile=myprofile",
    ]
    expected_args.extend(additional_args)

    kwargs = {
        "stdout": mock_subprocess.PIPE,
        "stderr": mock_subprocess.PIPE,
    }

    return expected_args, kwargs


def test_run_oscap_remediate_profile_only(mock_subprocess, monkeypatch):
    return run_oscap_remediate_profile(
        mock_subprocess, monkeypatch,
        ["myprofile", "my_ds.xml"],
        ["my_ds.xml"])


def test_run_oscap_remediate_with_ds(mock_subprocess, monkeypatch):
    return run_oscap_remediate_profile(
        mock_subprocess, monkeypatch,
        ["myprofile", "my_ds.xml", "my_ds_id"],
        ["--datastream-id=my_ds_id", "my_ds.xml"])


def test_run_oscap_remediate_with_ds_xccdf(mock_subprocess, monkeypatch):
    return run_oscap_remediate_profile(
        mock_subprocess, monkeypatch,
        ["myprofile", "my_ds.xml", "my_ds_id", "my_xccdf_id"],
        ["--datastream-id=my_ds_id", "--xccdf-id=my_xccdf_id", "my_ds.xml"])


def run_oscap_remediate_profile(
        mock_subprocess, monkeypatch,
        anaconda_remediate_args, oscap_remediate_args):
    mock_run_remediate(mock_subprocess, monkeypatch)
    common.run_oscap_remediate(* anaconda_remediate_args)

    expected_args = [
        "oscap", "xccdf", "eval", "--remediate",
        "--results=%s" % common.RESULTS_PATH,
        "--report=%s" % common.REPORT_PATH,
        "--profile=myprofile",
    ]
    expected_args.extend(oscap_remediate_args)

    kwargs = {
        "stdout": mock_subprocess.PIPE,
        "stderr": mock_subprocess.PIPE,
    }

    # it's impossible to check the preexec_func as it is an internal
    # function of the run_oscap_remediate function
    for arg in expected_args:
        assert arg in mock_subprocess.Popen.call_args[0][0]
        mock_subprocess.Popen.call_args[0][0].remove(arg)

    # nothing else should have been passed
    assert not mock_subprocess.Popen.call_args[0][0]

    for (key, val) in kwargs.items():
        assert kwargs[key] == mock_subprocess.Popen.call_args[1].pop(key)

    # plus the preexec_fn kwarg should have been passed
    assert "preexec_fn" in mock_subprocess.Popen.call_args[1]


def test_run_oscap_remediate_create_dir(mock_subprocess, monkeypatch):
    mock_run_remediate(mock_subprocess, monkeypatch)
    common.run_oscap_remediate("myprofile", "my_ds.xml")

    common.utils.ensure_dir_exists.assert_called_with(
        os.path.dirname(common.RESULTS_PATH))


def test_run_oscap_remediate_create_chroot_dir(mock_subprocess, monkeypatch):
    mock_run_remediate(mock_subprocess, monkeypatch)
    common.run_oscap_remediate("myprofile", "my_ds.xml", chroot="/mnt/test")

    chroot_dir = "/mnt/test" + os.path.dirname(common.RESULTS_PATH)
    common.utils.ensure_dir_exists.assert_called_with(chroot_dir)
