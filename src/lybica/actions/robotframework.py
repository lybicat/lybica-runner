import subprocess
import logging
import os


class RepeatRunningWrapper(object):
    ID = 101
    DESC = 'run robot suite repeatly'
    NAME = 'run_robotframework_repeatly'
    DEPENDS = []
    CRITICAL = True

    def start_action(self, context):
        # run the test and combine the output
        context.RUN_TIMES = os.getenv('RUN_TIMES', 1)
        logging.info('run times: %d' % context.RUN_TIMES)
        self.output_dir = context.WORKSPACE
        self.output_xml = os.path.join(self.output_dir, 'output.xml')
        context.CASE_ROOT = os.getenv('CASE_ROOT', '.')
        logging.info('CASE_ROOT: %s' % context.CASE_ROOT)
        output_files = self._run_test(context.RUN_TIMES, context.CASE_ROOT, self.output_dir)
        self._combine_output(output_files, self.output_xml)

    def _run_test(self, run_times, case_root, output_dir):
        for _round in xrange(run_times):
            logging.info('Round %d' % (_round + 1))
            subprocess.call(['pybot', '-L', 'Trace', '--report',\
                    'None', '--log', 'None', '-d', output_dir, '-o',\
                    'output-round-%d.xml' % (_round + 1), case_root])

    def _combine_output(self, output_files, dst_file):
        pass

    def stop_action(self, context):
        # parsing output.xml, generate log/report and post it to server
        self._generate_log_and_report(self.output_xml)
        summary = self._get_test_summary(self.output_xml)
        self._post_test_summary(summary)

    def _generate_log_and_report(self, output_xml):
        pass

    def _get_test_summary(self, output_xml):
        pass

    def _post_test_summary(self, summary):
        pass

