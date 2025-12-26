/**
 * 测试运行器
 */
import type { TestResult, TestSuite } from '../types'

export class TestRunner {
  private suites: TestSuite[] = []

  /**
   * 创建测试套件
   */
  createSuite(name: string): TestSuite {
    const suite: TestSuite = {
      name,
      tests: [],
      status: 'pending',
      duration: 0,
    }
    this.suites.push(suite)
    return suite
  }

  /**
   * 运行测试套件
   */
  async runSuite(
    suite: TestSuite,
    tests: Array<{ name: string; fn: () => Promise<void> | void }>
  ): Promise<TestSuite> {
    suite.status = 'running'
    const startTime = Date.now()

    for (const test of tests) {
      const testResult: TestResult = {
        name: test.name,
        status: 'running',
      }
      suite.tests.push(testResult)

      try {
        const testStart = Date.now()
        await test.fn()
        testResult.duration = Date.now() - testStart
        testResult.status = 'passed'
      } catch (error: any) {
        testResult.status = 'failed'
        testResult.error = error.message || String(error)
        testResult.details = error
      }
    }

    suite.duration = Date.now() - startTime
    suite.status = suite.tests.some((t) => t.status === 'failed') ? 'failed' : 'passed'

    return suite
  }

  /**
   * 获取所有测试套件
   */
  getSuites(): TestSuite[] {
    return this.suites
  }

  /**
   * 清除所有测试套件
   */
  clearSuites(): void {
    this.suites = []
  }

  /**
   * 获取测试统计
   */
  getStats(): {
    totalSuites: number
    totalTests: number
    passedTests: number
    failedTests: number
    totalDuration: number
  } {
    const totalSuites = this.suites.length
    const totalTests = this.suites.reduce((sum, suite) => sum + suite.tests.length, 0)
    const passedTests = this.suites.reduce(
      (sum, suite) => sum + suite.tests.filter((t) => t.status === 'passed').length,
      0
    )
    const failedTests = this.suites.reduce(
      (sum, suite) => sum + suite.tests.filter((t) => t.status === 'failed').length,
      0
    )
    const totalDuration = this.suites.reduce((sum, suite) => sum + suite.duration, 0)

    return {
      totalSuites,
      totalTests,
      passedTests,
      failedTests,
      totalDuration,
    }
  }
}

// 创建全局测试运行器实例
export const testRunner = new TestRunner()

/**
 * 测试辅助函数 - 断言
 */
export const assert = {
  equal: (actual: any, expected: any, message?: string) => {
    if (actual !== expected) {
      throw new Error(
        message || `Expected ${JSON.stringify(expected)} but got ${JSON.stringify(actual)}`
      )
    }
  },

  notEqual: (actual: any, expected: any, message?: string) => {
    if (actual === expected) {
      throw new Error(
        message || `Expected ${JSON.stringify(actual)} to not equal ${JSON.stringify(expected)}`
      )
    }
  },

  truthy: (value: any, message?: string) => {
    if (!value) {
      throw new Error(message || `Expected value to be truthy, got ${JSON.stringify(value)}`)
    }
  },

  falsy: (value: any, message?: string) => {
    if (value) {
      throw new Error(message || `Expected value to be falsy, got ${JSON.stringify(value)}`)
    }
  },

  throws: async (fn: () => Promise<any> | any, message?: string) => {
    try {
      await fn()
      throw new Error(message || 'Expected function to throw an error')
    } catch (error) {
      // Expected behavior
    }
  },

  contains: (haystack: any[], needle: any, message?: string) => {
    if (!haystack.includes(needle)) {
      throw new Error(
        message || `Expected array to contain ${JSON.stringify(needle)}`
      )
    }
  },
}
