---
name: aibdd.auto.java.e2e.starter
description: Java E2E Walking Skeleton 初始化。從 templates/ 讀取所有樣板檔案，填入專案參數後輸出到專案目錄，建立完整的 Spring Boot 3.2 + JPA + Cucumber 7.15 + Testcontainers 骨架。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[project-root]"
input: 專案根目錄路徑 + arguments.yml 參數
output: 完整的 Java E2E 專案骨架（可直接 mvn clean test 執行）
---

# 角色

Walking Skeleton 建構器。你從 templates/ 讀取樣板，替換 placeholder，寫入專案目錄。

---

# Placeholder 說明

所有 template 檔案使用 `{{PLACEHOLDER}}` 格式。以下是需要替換的變數：

| Placeholder | 來源 | 說明 | 範例 |
|-------------|------|------|------|
| `{{PROJECT_NAME}}` | 詢問使用者 | 專案顯示名稱 | `課程平台` |
| `{{PROJECT_DESCRIPTION}}` | 詢問使用者 | 專案描述 | `BDD Workshop - Java Spring Boot` |
| `{{GROUP_ID}}` | arguments.yml | Maven groupId | `com.wsa` |
| `{{ARTIFACT_ID}}` | arguments.yml | Maven artifactId | `platform` |
| `{{BASE_PACKAGE}}` | arguments.yml | Java base package | `com.wsa.platform` |
| `{{BASE_PACKAGE_PATH}}` | 從 BASE_PACKAGE 推導 | 檔案系統路徑（`.` 換成 `/`） | `com/wsa/platform` |
| `{{SPECS_ROOT_DIR}}` | arguments.yml | 規格檔案根目錄 | `specs` |

---

# 執行流程

## Step 1：收集參數

1. 讀取 `${PROJECT_ROOT}/specs/arguments.yml`（由 `/aibdd.kickoff` 產出）
2. 詢問使用者：
   - `PROJECT_NAME`：專案顯示名稱
   - `PROJECT_DESCRIPTION`：專案描述（建議預設值）
3. 推導：
   - `BASE_PACKAGE_PATH` = BASE_PACKAGE 中 `.` 換成 `/`（例：`com.wsa.platform` → `com/wsa/platform`）

## Step 2：建立目錄結構

根據 arguments.yml 建立所有目錄：

```
${PROJECT_ROOT}/
├── src/
│   ├── main/
│   │   ├── java/${BASE_PACKAGE_PATH}/
│   │   │   └── security/
│   │   └── resources/
│   │       └── db/migration/
│   └── test/
│       ├── java/${BASE_PACKAGE_PATH}/
│       │   ├── cucumber/
│       │   └── steps/
│       │       ├── common_then/
│       │       └── helpers/
│       └── resources/
│           └── features/
└── ${SPECS_ROOT_DIR}/
    ├── activities/
    ├── features/
    └── clarify/
```

## Step 3：讀取 templates，替換 placeholder，寫入專案

**檔案名對照表**（template 檔名用 `__` 表示目錄分隔符 `/`，`BASE_PKG` 表示 `${BASE_PACKAGE_PATH}`）：

| Template 檔案 | 輸出路徑 |
|---------------|----------|
| [templates/pom.xml](templates/pom.xml) | `pom.xml` |
| [templates/src__main__resources__application.yml](templates/src__main__resources__application.yml) | `src/main/resources/application.yml` |
| [templates/src__main__resources__application-test.yml](templates/src__main__resources__application-test.yml) | `src/main/resources/application-test.yml` |
| [templates/src__main__java__BASE_PKG__Application.java](templates/src__main__java__BASE_PKG__Application.java) | `src/main/java/${BASE_PACKAGE_PATH}/Application.java` |
| [templates/src__main__java__BASE_PKG__security__JwtTokenFilter.java](templates/src__main__java__BASE_PKG__security__JwtTokenFilter.java) | `src/main/java/${BASE_PACKAGE_PATH}/security/JwtTokenFilter.java` |
| [templates/src__main__java__BASE_PKG__security__CurrentUser.java](templates/src__main__java__BASE_PKG__security__CurrentUser.java) | `src/main/java/${BASE_PACKAGE_PATH}/security/CurrentUser.java` |
| [templates/src__test__java__BASE_PKG__RunCucumberTest.java](templates/src__test__java__BASE_PKG__RunCucumberTest.java) | `src/test/java/${BASE_PACKAGE_PATH}/RunCucumberTest.java` |
| [templates/src__test__java__BASE_PKG__cucumber__CucumberSpringConfiguration.java](templates/src__test__java__BASE_PKG__cucumber__CucumberSpringConfiguration.java) | `src/test/java/${BASE_PACKAGE_PATH}/cucumber/CucumberSpringConfiguration.java` |
| [templates/src__test__java__BASE_PKG__cucumber__ScenarioContext.java](templates/src__test__java__BASE_PKG__cucumber__ScenarioContext.java) | `src/test/java/${BASE_PACKAGE_PATH}/cucumber/ScenarioContext.java` |
| [templates/src__test__java__BASE_PKG__cucumber__DatabaseCleanupHook.java](templates/src__test__java__BASE_PKG__cucumber__DatabaseCleanupHook.java) | `src/test/java/${BASE_PACKAGE_PATH}/cucumber/DatabaseCleanupHook.java` |
| [templates/src__test__java__BASE_PKG__cucumber__JwtHelper.java](templates/src__test__java__BASE_PKG__cucumber__JwtHelper.java) | `src/test/java/${BASE_PACKAGE_PATH}/cucumber/JwtHelper.java` |
| [templates/src__test__java__BASE_PKG__steps__common_then__CommonThen.java](templates/src__test__java__BASE_PKG__steps__common_then__CommonThen.java) | `src/test/java/${BASE_PACKAGE_PATH}/steps/common_then/CommonThen.java` |
| [templates/src__test__java__BASE_PKG__steps__helpers__ScenarioContextHelper.java](templates/src__test__java__BASE_PKG__steps__helpers__ScenarioContextHelper.java) | `src/test/java/${BASE_PACKAGE_PATH}/steps/helpers/ScenarioContextHelper.java` |

## Step 4：驗證

完成後列出所有產出的檔案，確認：
1. 所有 template 都已寫入
2. 所有 `{{PLACEHOLDER}}` 都已替換（不應有殘留）
3. 目錄結構完整

---

# 與 Python E2E 的差異

| 項目 | Python E2E | Java E2E |
|------|------------|----------|
| Framework | FastAPI + SQLAlchemy | Spring Boot 3.2 + JPA |
| Test Runner | Behave | Cucumber 7.15 + JUnit Platform Suite |
| DB Container | Testcontainers（顯式管理） | Testcontainers（jdbc:tc: URL 自動管理） |
| Migration | Alembic | Flyway |
| Build Tool | pip + requirements.txt | Maven (pom.xml) |
| JWT | PyJWT | JJWT 0.12.3 |
| Package 結構 | 平坦目錄 + `__init__.py` | 分層 package（base package 可配置） |

---

# 安全規則

- **不覆蓋已存在的檔案**。若目標檔案已存在，跳過並回報。
- **不建立 feature-specific 的程式碼**（JPA Entities、Repositories、Services、Controllers、Step Definitions）。那些是 automation skills 的職責。
- **不執行 mvn install 或 flyway migrate**。骨架建完後，使用者自行執行。
- **DatabaseCleanupHook 中的 DELETE/RESET 語句需使用者在加入 Entity 後自行填入**。

---

# 完成後引導

```
Walking skeleton 已建立完成。

產出的檔案：（列出所有檔案）

下一步：
1. cd {{PROJECT_ROOT}} && mvn clean test
2. /aibdd.discovery — 開始需求探索
```
