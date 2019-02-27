# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from jenkinsflow.flow import serial, MessageRedefinedException
from .framework import api_select
from .framework.utils import lines_in, result_msg


def test_messages(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=1, serial=True)
        api.job('j21', max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=2, serial=True)
        api.job('j12', max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=3, serial=True)
        api.job('j22', max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=4)
        api.job('j23', max_fails=0, expect_invocations=1, invocation_delay=1.0, exec_time=2.00, expect_order=4)

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
        print(sout)
        assert lines_in(
            api_type, sout,
            "^--- Starting flow ---",
            "^Flow Invocation (1/1,1/1): ['jenkinsflow_test__messages__j11', ['jenkinsflow_test__messages__j21'], 'jenkinsflow_test__messages__j12', (",
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__messages__j11",
            "^SUCCESS: " + result_msg(api, "jenkinsflow_test__messages__j11"),
            "^**** Message 1 ****",
            "^Flow Invocation (1/1,1/1): ['jenkinsflow_test__messages__j21']",
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__messages__j21",
            "^SUCCESS: " + result_msg(api, "jenkinsflow_test__messages__j21"),
            "^Flow SUCCESS ['jenkinsflow_test__messages__j21'] after: ",
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__messages__j12",
            "^SUCCESS: " + result_msg(api, "jenkinsflow_test__messages__j12"),
            "^==== Message 2 ====",
            "^Flow Invocation (1/1,1/1): ('jenkinsflow_test__messages__j22', 'jenkinsflow_test__messages__j23')",
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__messages__j22",
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__messages__j23",
            "^SUCCESS: " + result_msg(api, "jenkinsflow_test__messages__j22"),
            "^SUCCESS: " + result_msg(api, "jenkinsflow_test__messages__j23"),
            "^Flow SUCCESS ('jenkinsflow_test__messages__j22', 'jenkinsflow_test__messages__j23') after: ",
            "^Flow SUCCESS ['jenkinsflow_test__messages__j11', ['jenkinsflow_test__messages__j21'], 'jenkinsflow_test__messages__j12', ('jenkinsflow_test__messages__j22', 'jenkinsflow_test__messages__j23')]",
        )


def test_messages_on_job(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j21', max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=1, serial=True)
        api.job('j12', max_fails=0, expect_invocations=1, invocation_delay=1.0, expect_order=2, serial=True)

        with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
            with ctrl1.serial() as sctrl2:
                with sctrl2.invoke('j21') as j21:
                    j21.message("*** Calling j21 ***")
            ctrl1.invoke('j12')

        sout, _ = capsys.readouterr()
        print(sout)
        assert lines_in(
            api_type, sout,
            "^--- Starting flow ---",
            "^Flow Invocation (1/1,1/1): [['jenkinsflow_test__messages_on_job__j21'], 'jenkinsflow_test__messages_on_job__j12'",
            "^Flow Invocation (1/1,1/1): ['jenkinsflow_test__messages_on_job__j21']",
            "^*** Calling j21 ***",
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__messages_on_job__j21",
            "^SUCCESS: " + result_msg(api, "jenkinsflow_test__messages_on_job__j21"),
            "^Flow SUCCESS ['jenkinsflow_test__messages_on_job__j21'] after: ",
            "^Job Invocation (1/1,1/1): http://x.x/job/jenkinsflow_test__messages_on_job__j12",
            "^SUCCESS: " + result_msg(api, "jenkinsflow_test__messages_on_job__j12"),
        )


def test_messages_redefined(api_type):
    with api_select.api(__file__, api_type) as api:
        api.flow_job()
        api.job('j11', max_fails=0, expect_invocations=0, invocation_delay=1.0, expect_order=None)
        api.job('j21', max_fails=0, expect_invocations=0, invocation_delay=1.0, expect_order=None)

        with raises(MessageRedefinedException) as exinfo:
            with serial(api, timeout=70, job_name_prefix=api.job_name_prefix) as ctrl1:
                ctrl1.invoke('j11')
                with ctrl1.serial() as sctrl2:
                    sctrl2.message("**** Message 1 ****")
                    sctrl2.invoke('j21')
                    sctrl2.message("New message")
                ctrl1.invoke('j12')

        assert str(exinfo.value) == "Existing message: '**** Message 1 ****', new message: 'New message'"
