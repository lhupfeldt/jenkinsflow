# Copyright (c) 2012 - 2014 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import serial, MessageRedefinedException
from .framework import mock_api
from .framework.utils import assert_lines_in


def test_messages(capsys):
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.01, max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=1, serial=True)
        api.job('j21', 0.01, max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=2, serial=True)
        api.job('j12', 0.01, max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=3, serial=True)
        api.job('j22', 0.01, max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=4)
        api.job('j23', 0.01, max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=4)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            ctrl1.invoke('j11')
            with ctrl1.serial() as sctrl2:
                sctrl2.message("**** Message 1 ****")
                sctrl2.invoke('j21')
            ctrl1.invoke('j12')
            with ctrl1.parallel() as pctrl:
                pctrl.message("==== Message 2 ====")
                pctrl.invoke('j22')
                pctrl.invoke('j23')

        sout, _ = capsys.readouterr()
        print sout
        assert_lines_in(
            sout,
            "--- Starting flow ---",
            "Invoking Flow (1/1,1/1): ['jenkinsflow_test__messages__j11', ['jenkinsflow_test__messages__j21'], 'jenkinsflow_test__messages__j12', (",
            "Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__messages__j11/",
            "SUCCESS: 'jenkinsflow_test__messages__j11' - build: http://x.x/job/jenkinsflow_test__messages__j11/",
            "**** Message 1 ****",
            "Invoking Flow (1/1,1/1): ['jenkinsflow_test__messages__j21']",
            "Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__messages__j21/",
            "SUCCESS: 'jenkinsflow_test__messages__j21' - build: http://x.x/job/jenkinsflow_test__messages__j21/",
            "SUCCESS ['jenkinsflow_test__messages__j21'] after: ",
            "Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__messages__j12/",
            "SUCCESS: 'jenkinsflow_test__messages__j12' - build: http://x.x/job/jenkinsflow_test__messages__j12/",
            "==== Message 2 ====",
            "Invoking Flow (1/1,1/1): ('jenkinsflow_test__messages__j22', 'jenkinsflow_test__messages__j23')",
            "Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__messages__j22/",
            "Invoking Job (1/1,1/1): http://x.x/job/jenkinsflow_test__messages__j23/",
            "SUCCESS: 'jenkinsflow_test__messages__j22' - build: http://x.x/job/jenkinsflow_test__messages__j22/",
            "SUCCESS: 'jenkinsflow_test__messages__j23' - build: http://x.x/job/jenkinsflow_test__messages__j23/",
            "SUCCESS ('jenkinsflow_test__messages__j22', 'jenkinsflow_test__messages__j23') after: ",
            "SUCCESS ['jenkinsflow_test__messages__j11', ['jenkinsflow_test__messages__j21'], 'jenkinsflow_test__messages__j12', ('jenkinsflow_test__messages__j22', 'jenkinsflow_test__messages__j23')]",
        )



def test_messages_redefined():
    with mock_api.api(__file__) as api:
        api.flow_job()
        api.job('j11', 0.01, max_fails=0, expect_invocations=0, invocation_delay=1.0, expect_order=None)
        api.job('j21', 0.01, max_fails=0, expect_invocations=0, invocation_delay=1.0, expect_order=None)

        with raises(MessageRedefinedException) as exinfo:
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke('j11')
                with ctrl1.serial() as sctrl2:
                    sctrl2.message("**** Message 1 ****")
                    sctrl2.invoke('j21')
                    sctrl2.message("New message")
                ctrl1.invoke('j12')

        assert exinfo.value.message == "Existing message: '**** Message 1 ****', new message: 'New message'"
