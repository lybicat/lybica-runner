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
        # run the test
        self.rpc = context.rpc
        context.RUN_TIMES = os.getenv('RUN_TIMES', 1)
        logging.info('run times: %d' % context.RUN_TIMES)
        self.output_dir = context.WORKSPACE
        self.output_xml = 'output.xml'
        self.task_id = context.TASK_ID
        context.CASE_ROOT = os.getenv('CASE_ROOT', '.')
        logging.info('CASE_ROOT: %s' % context.CASE_ROOT)
        self._run_test(context.RUN_TIMES, context.CASE_ROOT, self.output_dir)

    def _run_test(self, run_times, case_root, output_dir):
        for _round in xrange(run_times):
            logging.info('Round %d' % (_round + 1))
            subprocess.call(['pybot', '-L', 'Trace', '--report',\
                    'None', '--log', 'None', '-d', output_dir, '-o',\
                    'output-round-%d.xml' % (_round + 1), case_root])

    def _combine_output(self, output_dir, dst_file):
        # combine output files together
        logging.info('combine output files together')
        subprocess.call(['rebot', '-N', 'repeated', '-d', output_dir, '-o', dst_file, os.path.join(output_dir, 'output-round-*.xml')])

    def stop_action(self, context):
        # generate output.xml, log and report, post it to server
        self._combine_output(self.output_dir, self.output_xml)
        summary = self._get_test_summary(os.path.join(self.output_dir, self.output_xml))
        self._post_test_summary(summary)

    def _get_test_summary(self, output_xml):
        from robot.api import ExecutionResult
        result = ExecutionResult(output_xml)
        return {'passed': result.return_code == 0,
                'total': {
                    'total': result.statistics.total.all.total,
                    'passed': result.statistics.total.all.passed,
                    'failed': result.statistics.total.all.failed,
                    'elapsed': result.statistics.total.all.elapsed,
                },
                'tests': self._get_summary_of_a_suite(result.suite)
            }

    def _get_summary_of_a_suite(self, suite):
        result = []
        for test in suite.tests:
            result.append({'longname': test.longname,
                'passed': test.passed,
                'elapsed': test.elapsedtime})
        for subsuite in suite.suites:
            result.extend(self._get_summary_of_a_suite(subsuite))
        return result

    def _post_test_summary(self, summary):
        getattr(self.rpc, 'tasks__%s__result' % self.task_id)(summary)

