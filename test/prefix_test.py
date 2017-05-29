# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from jenkinsflow.flow import serial

from .framework import api_select


prefixed_jobs = """
serial flow: [
   job: 'top_quick1'
   serial flow: [
      job: 'top_x_quick2-1'
   ]

   serial flow: [
      job: 'top_x_quick2-2'
   ]

   serial flow: [
      job: 'top_x_quick2-3'
   ]

   job: 'top_quick3'
   parallel flow: (
      serial flow: [
         job: 'top_y_z_quick4a'
      ]

      serial flow: [
         job: 'quick4b'
      ]

      job: 'top_y_quick5'
   )

]
"""

def test_prefix(api_type, capsys):
    with api_select.api(__file__, api_type) as api:
        def job(name):
            api.job(name, max_fails=0, expect_invocations=0, expect_order=None, params=None)
    
        api.flow_job()
        job('quick1')
        index = 0
        for index in 1, 2, 3:
            job('x_quick2-' + str(index))
        job('quick3')
        job('y_z_quick4')
        job('y_quick5')

        with serial(api, timeout=70, report_interval=3, job_name_prefix='top_', just_dump=True) as ctrl1:
            ctrl1.invoke('quick1')
    
            for index in 1, 2, 3:
                with ctrl1.serial(timeout=20, report_interval=3, job_name_prefix='x_') as ctrl2:
                    ctrl2.invoke('quick2-' + str(index))
    
            ctrl1.invoke('quick3')
    
            with ctrl1.parallel(timeout=40, report_interval=3, job_name_prefix='y_') as ctrl2:
                with ctrl2.serial(timeout=40, report_interval=3, job_name_prefix='z_') as ctrl3a:
                    ctrl3a.invoke('quick4a')
                # Reset prefix
                with ctrl2.serial(timeout=40, report_interval=3, job_name_prefix=None) as ctrl3b:
                    ctrl3b.invoke('quick4b')

                ctrl2.invoke('quick5')

        sout, _ = capsys.readouterr()
        assert prefixed_jobs.strip() in sout
