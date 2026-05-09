# behave 在載入 step 模組時，globals 可能缺少 __name__，導致相對匯入失敗
if "__name__" not in globals():
    __name__ = "tests.features.steps"
if "__package__" not in globals():
    __package__ = "tests.features.steps"

# Subject Fork — PRD-034
from .subject_fork.aggregate_given import platform_subject  # noqa: F401
from .subject_fork.commands import api_calls  # noqa: F401
from .subject_fork.aggregate_then import db_assertions  # noqa: F401
from .subject_fork.readmodel_then import response_body  # noqa: F401

# Common Then
from .common_then import success  # noqa: F401
from .common_then import failure  # noqa: F401
from .common_then import failure_status_code  # noqa: F401
from .common_then import failure_with_reason  # noqa: F401
from .common_then import error_message  # noqa: F401
from .common_then import failure_with_error  # noqa: F401

# Auth — aggregate_given
from .auth.aggregate_given import users  # noqa: F401
from .auth.aggregate_given import auth_ui_state  # noqa: F401
from .auth.aggregate_given import user_auth_provider  # noqa: F401
from .auth.aggregate_given import user_has_journey  # noqa: F401
from .auth.aggregate_given import user_no_journey  # noqa: F401
from .auth.aggregate_given import user_role  # noqa: F401
from .auth.aggregate_given import user_subscription_and_role  # noqa: F401
from .auth.aggregate_given import user_subscription  # noqa: F401
from .auth.aggregate_given import user_verified  # noqa: F401
from .auth.aggregate_given import user_status  # noqa: F401
from .auth.aggregate_given import user_google_sso  # noqa: F401

# Auth — commands
from .auth.commands import check_password_strength  # noqa: F401
from .auth.commands import auth_ui_actions  # noqa: F401
from .auth.commands import resend_verification_ui  # noqa: F401
from .auth.commands import forgot_password  # noqa: F401
from .auth.commands import reset_password  # noqa: F401
from .auth.commands import google_sso  # noqa: F401
from .auth.commands import login  # noqa: F401
from .auth.commands import login_by_email  # noqa: F401
from .auth.commands import register  # noqa: F401
from .auth.commands import register_no_terms  # noqa: F401
from .auth.commands import user_action  # noqa: F401
from .auth.commands import verify_email  # noqa: F401
from .auth.commands import verify_email_invalid  # noqa: F401
from .auth.commands import resend_verification  # noqa: F401
from .auth.commands import unauthenticated_access  # noqa: F401
from .auth.commands import admin_api_access  # noqa: F401

# Auth — aggregate_then
from .auth.aggregate_then import auth_provider_linked  # noqa: F401
from .auth.aggregate_then import auth_provider_noted  # noqa: F401
from .auth.aggregate_then import gcs_files_deleted  # noqa: F401
from .auth.aggregate_then import jwt_revoked  # noqa: F401
from .auth.aggregate_then import new_account_created  # noqa: F401
from .auth.aggregate_then import no_account_leak  # noqa: F401
from .auth.aggregate_then import redis_cache_cleared  # noqa: F401
from .auth.aggregate_then import reset_email_sent  # noqa: F401
from .auth.aggregate_then import reset_link_expires  # noqa: F401
from .auth.aggregate_then import user_data_removed  # noqa: F401
from .auth.aggregate_then import verification_email_sent  # noqa: F401
from .auth.aggregate_then import account_status_updated  # noqa: F401
from .auth.aggregate_then import account_status_unchanged  # noqa: F401

# Auth — readmodel_then
from .auth.readmodel_then import jwt_token  # noqa: F401
from .auth.readmodel_then import auth_ui  # noqa: F401
from .auth.readmodel_then import login_no_error  # noqa: F401
from .auth.readmodel_then import navbar_not_shows  # noqa: F401
from .auth.readmodel_then import navbar_shows  # noqa: F401
from .auth.readmodel_then import password_strength  # noqa: F401
from .auth.readmodel_then import redirect_to  # noqa: F401
from .auth.readmodel_then import response_contains  # noqa: F401
from .auth.readmodel_then import user_info  # noqa: F401


# Resource — aggregate_given
from .resource.aggregate_given import user_subject  # noqa: F401
from .resource.aggregate_given import chunked_upload_init  # noqa: F401
from .resource.aggregate_given import chunked_upload_partial  # noqa: F401
from .resource.aggregate_given import chunked_upload_all  # noqa: F401
from .resource.aggregate_given import resource_with_chunks  # noqa: F401
from .resource.aggregate_given import seed_resource_with_chunks  # noqa: F401

# Resource — commands
from .resource.commands import upload_file  # noqa: F401
from .resource.commands import upload_file_with_size  # noqa: F401
from .resource.commands import upload_image  # noqa: F401
from .resource.commands import upload_pdf  # noqa: F401
from .resource.commands import submit_youtube  # noqa: F401
from .resource.commands import upload_missing_params  # noqa: F401
from .resource.commands import init_chunked_upload  # noqa: F401
from .resource.commands import query_chunked_progress  # noqa: F401
from .resource.commands import complete_chunked_upload  # noqa: F401
from .resource.commands import query_chunks  # noqa: F401
from .resource.commands import resource_detail  # noqa: F401
from .resource.commands import upload_chunk  # noqa: F401
from .resource.commands import query_resource_list  # noqa: F401
from .resource.commands import upload_special_pdf  # noqa: F401
from .resource.aggregate_then import no_resource_created  # noqa: F401
from .resource.aggregate_then import resource_status_and_error  # noqa: F401
from .resource.commands import trigger_background_processing  # noqa: F401
from .resource.aggregate_given import failed_resource  # noqa: F401

# Resource — readmodel_then
from .resource.readmodel_then import resource_status  # noqa: F401
from .resource.readmodel_then import processing_engine  # noqa: F401
from .resource.readmodel_then import implicit_consent  # noqa: F401
from .resource.readmodel_then import resource_type  # noqa: F401
from .resource.readmodel_then import can_resume_upload  # noqa: F401
from .resource.readmodel_then import resource_file_size  # noqa: F401
from .resource.readmodel_then import chunk_count  # noqa: F401
from .resource.readmodel_then import resource_detail_response  # noqa: F401
from .resource.readmodel_then import error_message_in_list  # noqa: F401

# Resource Parse — EPIC-035
from .resource_parse.aggregate_given import parsed_resource  # noqa: F401
from .resource_parse.aggregate_given import parse_quota_used  # noqa: F401
from .resource_parse.aggregate_given import personal_question  # noqa: F401
from .resource_parse.aggregate_given import scaffolded_resource  # noqa: F401
from .resource_parse.aggregate_given import personal_question_with_node  # noqa: F401
from .resource_parse.commands import parse_actions  # noqa: F401
from .resource_parse.commands import blind_answer_actions  # noqa: F401
from .resource_parse.commands import scaffold_actions  # noqa: F401
from .resource_parse.commands import practice_submit_actions  # noqa: F401
from .resource_parse.readmodel_then import parse_response  # noqa: F401
from .resource_parse.aggregate_then import questions_by_resource  # noqa: F401
from .resource_parse.aggregate_then import question_explanation  # noqa: F401
from .resource_parse.aggregate_then import scaffold_response  # noqa: F401
from .resource_parse.aggregate_then import reference_answer_populated  # noqa: F401
from .resource_parse.commands import generate_reference_answer  # noqa: F401

# Common Then — EPIC-035 additions
from .common_then import status_and_bracket_error  # noqa: F401

# Knowledge Map — aggregate_given
from .knowledge_map.aggregate_given import knowledge_node_data  # noqa: F401
from .knowledge_map.aggregate_given import knowledge_map_ui_state  # noqa: F401
from .knowledge_map.aggregate_given import node_initial_mastery  # noqa: F401
from .knowledge_map.aggregate_given import subject_library  # noqa: F401
from .knowledge_map.aggregate_given import user_logged_in_multi_subject  # noqa: F401
from .knowledge_map.aggregate_given import resource_processing  # noqa: F401
from .knowledge_map.aggregate_given import youtube_processing  # noqa: F401
from .knowledge_map.aggregate_given import knowledge_map_generated  # noqa: F401
from .knowledge_map.aggregate_given import short_content_pdf  # noqa: F401
from .knowledge_map.aggregate_given import exam_subjects  # noqa: F401
from .knowledge_map.aggregate_given import user_exam_subjects  # noqa: F401
from .knowledge_map.aggregate_given import subject_knowledge_nodes  # noqa: F401
from .knowledge_map.aggregate_given import user_single_subject  # noqa: F401
from .knowledge_map.aggregate_given import user_node_followup_count  # noqa: F401
from .knowledge_map.aggregate_given import user_coach_quota  # noqa: F401
from .knowledge_map.aggregate_given import basic_coach_quota  # noqa: F401
from .knowledge_map.aggregate_given import resource_scaffolds  # noqa: F401

# Knowledge Map — commands
from .knowledge_map.commands import ai_coach_input  # noqa: F401
from .knowledge_map.commands import knowledge_map_ui_actions  # noqa: F401
from .knowledge_map.commands import ai_coach_input_locked  # noqa: F401
from .knowledge_map.commands import answer_questions_correctly  # noqa: F401
from .knowledge_map.commands import click_knowledge_node  # noqa: F401
from .knowledge_map.commands import query_node_scaffolds  # noqa: F401
from .knowledge_map.commands import enter_knowledge_map  # noqa: F401
from .knowledge_map.commands import switch_subject  # noqa: F401
from .knowledge_map.commands import complete_resource_parsing  # noqa: F401
from .knowledge_map.commands import complete_video_parsing  # noqa: F401
from .knowledge_map.commands import attempt_map_generation  # noqa: F401
from .knowledge_map.commands import select_subject  # noqa: F401
from .knowledge_map.commands import view_knowledge_tree  # noqa: F401
from .knowledge_map.commands import view_node_source  # noqa: F401
from .knowledge_map.commands import click_node  # noqa: F401
from .knowledge_map.commands import coach_followup  # noqa: F401
from .knowledge_map.commands import coach_input  # noqa: F401
from .knowledge_map.commands import long_input  # noqa: F401

# Knowledge Map — aggregate_then
from .knowledge_map.aggregate_then import knowledge_tree_created  # noqa: F401
from .knowledge_map.aggregate_then import knowledge_tree_with_timestamps  # noqa: F401
from .knowledge_map.aggregate_then import resource_status_updated  # noqa: F401
from .knowledge_map.aggregate_then import tree_hierarchy  # noqa: F401
from .knowledge_map.aggregate_then import leaf_node_source  # noqa: F401
from .knowledge_map.aggregate_then import coach_quota_remaining  # noqa: F401
from .knowledge_map.aggregate_then import basic_quota_remaining  # noqa: F401

# Knowledge Map — readmodel_then
from .knowledge_map.readmodel_then import achievement_animation  # noqa: F401
from .knowledge_map.readmodel_then import scaffolds_list  # noqa: F401
from .knowledge_map.readmodel_then import knowledge_map_ui  # noqa: F401
from .knowledge_map.readmodel_then import coach_response_rendered  # noqa: F401
from .knowledge_map.readmodel_then import knowledge_tree_displayed  # noqa: F401
from .knowledge_map.readmodel_then import main_panel_layout  # noqa: F401
from .knowledge_map.readmodel_then import markdown_highlight  # noqa: F401
from .knowledge_map.readmodel_then import model_switched  # noqa: F401
from .knowledge_map.readmodel_then import node_color_updated  # noqa: F401
from .knowledge_map.readmodel_then import paywall_blur  # noqa: F401
from .knowledge_map.readmodel_then import quota_deducted  # noqa: F401
from .knowledge_map.readmodel_then import resource_list_loaded  # noqa: F401
from .knowledge_map.readmodel_then import side_panel_layout  # noqa: F401
from .knowledge_map.readmodel_then import source_citation_displayed  # noqa: F401
from .knowledge_map.readmodel_then import upgrade_prompt  # noqa: F401
from .knowledge_map.readmodel_then import toast_notification  # noqa: F401
from .knowledge_map.readmodel_then import hint_message  # noqa: F401
from .knowledge_map.readmodel_then import knowledge_nodes_displayed  # noqa: F401
from .knowledge_map.readmodel_then import no_other_subject_nodes  # noqa: F401
from .knowledge_map.readmodel_then import response_contains_table  # noqa: F401
from .knowledge_map.readmodel_then import coach_source_info  # noqa: F401
from .knowledge_map.readmodel_then import coach_markdown_content  # noqa: F401
from .knowledge_map.readmodel_then import upgrade_prompt_info  # noqa: F401
from .knowledge_map.readmodel_then import streaming_response  # noqa: F401
from .knowledge_map.readmodel_then import model_indicator  # noqa: F401
from .knowledge_map.readmodel_then import mastery_colors  # noqa: F401
from .knowledge_map.readmodel_then import color_rules  # noqa: F401
from .knowledge_map.readmodel_then import basic_coach_response  # noqa: F401
from .knowledge_map.readmodel_then import safety_classification  # noqa: F401
from .knowledge_map.readmodel_then import ai_coach_reply  # noqa: F401

# Exam — aggregate_given
from .exam.aggregate_given import resources  # noqa: F401
from .exam.aggregate_given import bloom_source as _bloom_source_given  # noqa: F401
from .exam.aggregate_given import knowledge_nodes  # noqa: F401
from .exam.aggregate_given import exam_task_created  # noqa: F401
from .exam.aggregate_given import resources_with_nodes  # noqa: F401
from .exam.aggregate_given import knowledge_nodes_simple  # noqa: F401
from .exam.aggregate_given import prompt_templates  # noqa: F401
from .exam.aggregate_given import exam_config_submitted  # noqa: F401
from .exam.aggregate_given import user_profile  # noqa: F401
from .exam.aggregate_given import user_profile_empty  # noqa: F401
from .exam.aggregate_given import stage_given  # noqa: F401
from .exam.aggregate_given import admin_login  # noqa: F401
from .exam.aggregate_given import exam_task_with_id  # noqa: F401
from .exam.aggregate_given import bloom_stats  # noqa: F401
from .exam.aggregate_given import user_learning_journey  # noqa: F401
from .exam.aggregate_given import subject_historical_questions  # noqa: F401
from .exam.aggregate_given import subject_node_limited_questions  # noqa: F401
from .exam.aggregate_given import user_no_resources  # noqa: F401
from .exam.aggregate_given import subject_historical_nodes  # noqa: F401

# Exam — commands
from .exam.commands import submit_exam_no_nodes  # noqa: F401
from .exam.commands import submit_exam_single_node  # noqa: F401
from .exam.commands import submit_exam_two_nodes  # noqa: F401
from .exam.commands import submit_exam_with_difficulty  # noqa: F401
from .exam.commands import submit_exam_single_with_difficulty  # noqa: F401
from .exam.commands import ai_generate_stages  # noqa: F401
from .exam.commands import ai_generate_complete  # noqa: F401
from .exam.commands import ai_generate_start  # noqa: F401
from .exam.commands import stage_prompt_inputs  # noqa: F401
from .exam.commands import prompt_template_commands  # noqa: F401
from .exam.commands import ai_retry_commands  # noqa: F401
from .exam.commands import submit_exam_table  # noqa: F401
from .exam.commands import submit_exam_by_node_name  # noqa: F401
from .exam.commands import submit_exam_custom_bloom  # noqa: F401
from .exam.commands import submit_exam_question_types  # noqa: F401
from .exam.commands import select_resource  # noqa: F401

# Exam — query
from .exam.query import select_subject_filter  # noqa: F401
from .exam.query import recent_failures  # noqa: F401

# Exam — aggregate_then
from .exam.aggregate_then import exam_task_status  # noqa: F401

# Exam — readmodel_then
from .exam.readmodel_then import subject_resources_filtered  # noqa: F401
from .exam.readmodel_then import exclude_other_subject  # noqa: F401
from .exam.readmodel_then import sse_progress_started  # noqa: F401
from .exam.readmodel_then import sse_progress_events  # noqa: F401
from .exam.readmodel_then import response_exam_id  # noqa: F401
from .exam.readmodel_then import response_question_count  # noqa: F401
from .exam.readmodel_then import stages_executed  # noqa: F401
from .exam.readmodel_then import personalization_prompts  # noqa: F401
from .exam.readmodel_then import stage1_output  # noqa: F401
from .exam.readmodel_then import stage1_prompt_then  # noqa: F401
from .exam.readmodel_then import stage2_output  # noqa: F401
from .exam.readmodel_then import stage3_output  # noqa: F401
from .exam.readmodel_then import stage4_output  # noqa: F401
from .exam.readmodel_then import prompt_template_then  # noqa: F401
from .exam.readmodel_then import retry_then  # noqa: F401
from .exam.readmodel_then import bloom_source  # noqa: F401
from .exam.readmodel_then import bloom_applied  # noqa: F401
from .exam.readmodel_then import default_bloom_applied  # noqa: F401
from .exam.readmodel_then import exam_contains_questions  # noqa: F401
from .exam.readmodel_then import all_historical  # noqa: F401
from .exam.readmodel_then import no_ai_service  # noqa: F401
from .exam.readmodel_then import response_hint  # noqa: F401
from .exam.readmodel_then import historical_ratio  # noqa: F401
from .exam.readmodel_then import standard_ratio  # noqa: F401
from .exam.readmodel_then import bloom_distribution_custom  # noqa: F401
from .exam.readmodel_then import bloom_source_not_custom  # noqa: F401
from .exam.readmodel_then import historical_questions_only  # noqa: F401
from .exam.readmodel_then import exam_question_types  # noqa: F401
from .exam.readmodel_then import exam_hard_difficulty  # noqa: F401

# Mock Exam — aggregate_given
from .mock_exam.aggregate_given import exams  # noqa: F401
from .mock_exam.aggregate_given import questions  # noqa: F401
from .mock_exam.aggregate_given import saved_answers  # noqa: F401
from .mock_exam.aggregate_given import exam_started  # noqa: F401
from .mock_exam.aggregate_given import exam_ready  # noqa: F401

# Mock Exam — commands
from .mock_exam.commands import start_exam  # noqa: F401
from .mock_exam.commands import select_answer  # noqa: F401
from .mock_exam.commands import mark_review  # noqa: F401
from .mock_exam.commands import submit_exam  # noqa: F401
from .mock_exam.commands import resume_exam  # noqa: F401
from .mock_exam.commands import fill_in_answer  # noqa: F401
from .mock_exam.commands import exam_ui_actions  # noqa: F401

# Mock Exam — aggregate_then
from .mock_exam.aggregate_then import exam_status  # noqa: F401
from .mock_exam.aggregate_then import exam_started_at  # noqa: F401
from .mock_exam.aggregate_then import answer_saved  # noqa: F401
from .mock_exam.aggregate_then import review_marked  # noqa: F401

# Mock Exam — readmodel_then
from .mock_exam.readmodel_then import resume_answer  # noqa: F401
from .mock_exam.readmodel_then import exam_ui  # noqa: F401

# Exam Result — aggregate_given
from .exam_result.aggregate_given import history_exams  # noqa: F401
from .exam_result.aggregate_given import node_stats  # noqa: F401
from .exam_result.aggregate_given import score_history  # noqa: F401

# Exam Result — commands
from .exam_result.commands import view_result  # noqa: F401
from .exam_result.commands import view_node_analysis  # noqa: F401
from .exam_result.commands import result_ui_actions  # noqa: F401

# Exam Result — readmodel_then
from .exam_result.readmodel_then import result_fields  # noqa: F401
from .exam_result.readmodel_then import node_analysis  # noqa: F401
from .exam_result.readmodel_then import result_ui  # noqa: F401

# Wrong Answer — aggregate_given
from .wrong_answer.aggregate_given import exam_wrong_records  # noqa: F401
from .wrong_answer.aggregate_given import user_profile  # noqa: F401
from .wrong_answer.aggregate_given import historical_wrong  # noqa: F401
from .wrong_answer.aggregate_given import cooldown_history  # noqa: F401
from .wrong_answer.aggregate_given import learning_history  # noqa: F401
from .wrong_answer.aggregate_given import review_page_state  # noqa: F401
from .wrong_answer.aggregate_given import wrong_review_mastery_setup  # noqa: F401
from .wrong_answer.commands import wrong_review_resubmit  # noqa: F401

# Wrong Answer — commands
from .wrong_answer.commands import filter_by_subject  # noqa: F401
from .wrong_answer.commands import view_wrong_answers  # noqa: F401
from .wrong_answer.commands import ai_coach  # noqa: F401
from .wrong_answer.commands import ai_coach_generic  # noqa: F401
from .wrong_answer.commands import advanced_coach  # noqa: F401
from .wrong_answer.commands import review_ui_actions  # noqa: F401

# Wrong Answer — readmodel_then
from .wrong_answer.readmodel_then import subject_filter  # noqa: F401
from .wrong_answer.readmodel_then import basic_info  # noqa: F401
from .wrong_answer.readmodel_then import locked_state  # noqa: F401
from .wrong_answer.readmodel_then import full_analysis  # noqa: F401
from .wrong_answer.readmodel_then import source_citation  # noqa: F401
from .wrong_answer.readmodel_then import streaming_response  # noqa: F401
from .wrong_answer.readmodel_then import ai_coach_content  # noqa: F401
from .wrong_answer.readmodel_then import ai_coach_tone  # noqa: F401
from .wrong_answer.readmodel_then import ai_coach_analogy  # noqa: F401
from .wrong_answer.readmodel_then import ai_coach_technical  # noqa: F401
from .wrong_answer.readmodel_then import ai_coach_default_tone  # noqa: F401
from .wrong_answer.readmodel_then import ai_coach_history  # noqa: F401
from .wrong_answer.readmodel_then import ai_coach_reply_contains  # noqa: F401
from .wrong_answer.readmodel_then import ai_coach_cooldown  # noqa: F401
from .wrong_answer.readmodel_then import disclaimer  # noqa: F401
from .wrong_answer.readmodel_then import advanced_coach_analysis  # noqa: F401
from .wrong_answer.readmodel_then import review_ui  # noqa: F401

# Subscription — aggregate_given
from .subscription.aggregate_given import invoices  # noqa: F401

# Subscription — commands
from .subscription.commands import subscribe  # noqa: F401
from .subscription.commands import subscribe_empty  # noqa: F401
from .subscription.commands import view_subscription  # noqa: F401
from .subscription.commands import upgrade  # noqa: F401
from .subscription.commands import downgrade  # noqa: F401
from .subscription.commands import cancel  # noqa: F401
from .subscription.commands import view_invoices  # noqa: F401

# Subscription — aggregate_then
from .subscription.aggregate_then import subscription_plan  # noqa: F401
from .subscription.aggregate_then import subscription_status  # noqa: F401

# Subscription — readmodel_then
from .subscription.readmodel_then import subscription_info  # noqa: F401
from .subscription.readmodel_then import downgrade_info  # noqa: F401
from .subscription.readmodel_then import invoice_list  # noqa: F401

# Schedule — aggregate_given
from .schedule.aggregate_given import exam_subjects  # noqa: F401
from .schedule.aggregate_given import question_stats  # noqa: F401
from .schedule.aggregate_given import exam_date_empty  # noqa: F401
from .schedule.aggregate_given import today_date  # noqa: F401
from .schedule.aggregate_given import exam_date_override  # noqa: F401

# Schedule — commands
from .schedule.commands import view_schedule  # noqa: F401
from .schedule.commands import init_schedule  # noqa: F401
from .schedule.commands import calculate_mode  # noqa: F401

# Schedule — readmodel_then
from .schedule.readmodel_then import learning_mode  # noqa: F401
from .schedule.readmodel_then import schedule_recommendations  # noqa: F401

# B2B — aggregate_given
from .b2b.aggregate_given import institutions  # noqa: F401
from .b2b.aggregate_given import student_groups  # noqa: F401
from .b2b.aggregate_given import group_members  # noqa: F401
from .b2b.aggregate_given import early_warning_rules  # noqa: F401
from .b2b.aggregate_given import edu_students  # noqa: F401
from .b2b.aggregate_given import dpa_state  # noqa: F401
from .b2b.aggregate_given import org_exam_config  # noqa: F401
from .b2b.aggregate_given import student_scores  # noqa: F401
from .b2b.aggregate_given import weakness_data  # noqa: F401
from .b2b.aggregate_given import existing_user_with_plan  # noqa: F401
from .b2b.aggregate_given import student_competency_data  # noqa: F401
from .b2b.aggregate_given import student_exam_history  # noqa: F401
from .b2b.aggregate_given import student_exam_single  # noqa: F401
from .b2b.aggregate_given import student_wrong_answers  # noqa: F401
from .b2b.aggregate_given import student_no_exams  # noqa: F401

# B2B — commands
from .b2b.commands import access_admin  # noqa: F401
from .b2b.commands import import_csv_count  # noqa: F401
from .b2b.commands import import_csv_table  # noqa: F401
from .b2b.commands import import_csv_consent  # noqa: F401
from .b2b.commands import view_dpa  # noqa: F401
from .b2b.commands import view_students  # noqa: F401
from .b2b.commands import assign_exam  # noqa: F401
from .b2b.commands import view_heatmap  # noqa: F401
from .b2b.commands import view_error_ranking  # noqa: F401
from .b2b.commands import view_health_kpi  # noqa: F401
from .b2b.commands import view_early_warning  # noqa: F401
from .b2b.commands import update_warning_rules  # noqa: F401
from .b2b.commands import view_student_competency  # noqa: F401
from .b2b.commands import request_ai_suggestion  # noqa: F401
from .b2b.commands import generate_remediation  # noqa: F401
from .b2b.commands import view_student_report  # noqa: F401
from .b2b.commands import assign_remediation  # noqa: F401
from .b2b.commands import view_remediation_defaults  # noqa: F401
from .b2b.commands import delete_group  # noqa: F401
from .b2b.commands import batch_remove_students  # noqa: F401
from .b2b.commands import remove_student  # noqa: F401
from .b2b.commands import b2b_ui_actions  # noqa: F401

# B2B — aggregate_then
from .b2b.aggregate_then import new_student_accounts  # noqa: F401
from .b2b.aggregate_then import monthly_surcharge  # noqa: F401
from .b2b.aggregate_then import user_plan_check  # noqa: F401
from .b2b.aggregate_then import invitation_email  # noqa: F401
from .b2b.aggregate_then import group_member_count  # noqa: F401
from .b2b.aggregate_then import warning_rules  # noqa: F401
from .b2b.aggregate_then import group_not_exists  # noqa: F401
from .b2b.aggregate_then import student_still_in_org  # noqa: F401
from .b2b.aggregate_then import student_not_in_org  # noqa: F401
from .b2b.aggregate_then import org_student_count  # noqa: F401
from .b2b.aggregate_then import remediation_assignment  # noqa: F401

# B2B — readmodel_then
from .b2b.readmodel_then import institution_name  # noqa: F401
# Note: b2b response_contains removed — duplicate of knowledge_map response_contains_table
from .b2b.readmodel_then import empty_students  # noqa: F401
from .b2b.readmodel_then import empty_hint  # noqa: F401
from .b2b.readmodel_then import onboarding_guide  # noqa: F401
from .b2b.readmodel_then import assignment_record  # noqa: F401
from .b2b.readmodel_then import heatmap_matrix  # noqa: F401
from .b2b.readmodel_then import error_ranking  # noqa: F401
from .b2b.readmodel_then import early_warning_student  # noqa: F401
from .b2b.readmodel_then import student_competency  # noqa: F401
from .b2b.readmodel_then import ai_suggestions  # noqa: F401
from .b2b.readmodel_then import student_trend  # noqa: F401
from .b2b.readmodel_then import remediation_exam  # noqa: F401
from .b2b.readmodel_then import student_report_fields  # noqa: F401
from .b2b.readmodel_then import exam_history  # noqa: F401
from .b2b.readmodel_then import remediation_result  # noqa: F401
from .b2b.readmodel_then import remediation_defaults_check  # noqa: F401
from .b2b.readmodel_then import ai_suggestions_advanced  # noqa: F401
from .b2b.readmodel_then import b2b_ui  # noqa: F401

# Resource Library — aggregate_given
from .resource_lib.aggregate_given import resources as rl_resources  # noqa: F401

# Resource Library — commands
from .resource_lib.commands import list_resources  # noqa: F401
from .resource_lib.commands import delete_resource  # noqa: F401
from .resource_lib.commands import search_resources  # noqa: F401
from .resource_lib.commands import reparse_resource  # noqa: F401

# Resource Library — readmodel_then
from .resource_lib.readmodel_then import resource_count  # noqa: F401

# Resource Library — aggregate_then
from .resource_lib.aggregate_then import resource_status  # noqa: F401

# Onboarding — aggregate_given
from .onboarding.aggregate_given import onboarding_state  # noqa: F401
from .onboarding.aggregate_given import subject_categories  # noqa: F401
from .onboarding.aggregate_given import onboarding_not_completed  # noqa: F401
from .onboarding.aggregate_given import onboarding_in_progress  # noqa: F401
from .onboarding.aggregate_given import enter_onboarding  # noqa: F401
from .onboarding.aggregate_given import enter_step2  # noqa: F401
from .onboarding.aggregate_given import selected_subjects  # noqa: F401
from .onboarding.aggregate_given import enter_step3  # noqa: F401
from .onboarding.aggregate_given import completed_steps  # noqa: F401
from .onboarding.aggregate_given import at_step4  # noqa: F401
from .onboarding.aggregate_given import onboarding_with_subjects  # noqa: F401
from .onboarding.aggregate_given import current_subject  # noqa: F401
from .onboarding.aggregate_given import at_profile_page  # noqa: F401
from .onboarding.aggregate_given import archived_journey  # noqa: F401
from .onboarding.aggregate_given import parent_child_subjects  # noqa: F401
from .onboarding.aggregate_given import subject_in_category  # noqa: F401
from .onboarding.aggregate_given import subject_with_level  # noqa: F401
from .onboarding.aggregate_given import current_category  # noqa: F401
from .onboarding.aggregate_given import custom_subject_owner  # noqa: F401

# Onboarding — commands
from .onboarding.commands import view_status  # noqa: F401
from .onboarding.commands import submit_onboarding  # noqa: F401
from .onboarding.commands import add_subject  # noqa: F401
from .onboarding.commands import archive_subject  # noqa: F401
from .onboarding.commands import skip_subject_next  # noqa: F401
from .onboarding.commands import select_category  # noqa: F401
from .onboarding.commands import search_subject  # noqa: F401
from .onboarding.commands import select_subjects  # noqa: F401
from .onboarding.commands import remove_subject_onboarding  # noqa: F401
from .onboarding.commands import set_preferences  # noqa: F401
from .onboarding.commands import custom_study_time  # noqa: F401
from .onboarding.commands import enter_step4  # noqa: F401
from .onboarding.commands import start_journey  # noqa: F401
from .onboarding.commands import add_subject_dashboard  # noqa: F401
from .onboarding.commands import add_subject_post_onboarding  # noqa: F401
from .onboarding.commands import remove_subject_account  # noqa: F401
from .onboarding.commands import confirm_remove  # noqa: F401
from .onboarding.commands import view_profile  # noqa: F401
from .onboarding.commands import update_profile  # noqa: F401
from .onboarding.commands import query_available_subjects  # noqa: F401
from .onboarding.commands import add_subject_table  # noqa: F401
from .onboarding.commands import remove_and_confirm  # noqa: F401
from .onboarding.commands import query_subject_list  # noqa: F401
from .onboarding.commands import add_custom_subject  # noqa: F401
from .onboarding.commands import switch_subject_level  # noqa: F401
from .onboarding.commands import click_edit_section  # noqa: F401
from .onboarding.commands import switch_category  # noqa: F401
from .onboarding.commands import create_custom_subject  # noqa: F401

# Onboarding — aggregate_then
from .onboarding.aggregate_then import journeys_created  # noqa: F401
from .onboarding.aggregate_then import onboarding_completed  # noqa: F401
from .onboarding.aggregate_then import journey_created  # noqa: F401
from .onboarding.aggregate_then import switcher_added  # noqa: F401
from .onboarding.aggregate_then import journey_unaffected  # noqa: F401
from .onboarding.aggregate_then import journey_archived  # noqa: F401
from .onboarding.aggregate_then import switcher_removed  # noqa: F401
from .onboarding.aggregate_then import profile_updated  # noqa: F401
from .onboarding.aggregate_then import journey_active  # noqa: F401
from .onboarding.aggregate_then import journey_contains  # noqa: F401
from .onboarding.aggregate_then import journey_archived_by_name  # noqa: F401
from .onboarding.aggregate_then import active_journey_excludes  # noqa: F401
from .onboarding.aggregate_then import custom_subject_assertions  # noqa: F401

# Onboarding — readmodel_then
from .onboarding.readmodel_then import onboarding_status  # noqa: F401
from .onboarding.readmodel_then import welcome_animation  # noqa: F401
from .onboarding.readmodel_then import input_fields  # noqa: F401
from .onboarding.readmodel_then import age_range  # noqa: F401
from .onboarding.readmodel_then import education_options  # noqa: F401
from .onboarding.readmodel_then import hint_text  # noqa: F401
from .onboarding.readmodel_then import skip_option  # noqa: F401
from .onboarding.readmodel_then import category_subjects  # noqa: F401
from .onboarding.readmodel_then import search_results  # noqa: F401
from .onboarding.readmodel_then import selected_subjects_count  # noqa: F401
from .onboarding.readmodel_then import remove_button  # noqa: F401
from .onboarding.readmodel_then import selected_subjects_only  # noqa: F401
from .onboarding.readmodel_then import preferences_saved  # noqa: F401
from .onboarding.readmodel_then import study_time  # noqa: F401
from .onboarding.readmodel_then import summary_display  # noqa: F401
from .onboarding.readmodel_then import summary_subjects_correct  # noqa: F401
from .onboarding.readmodel_then import start_button  # noqa: F401
from .onboarding.readmodel_then import confirm_prompt  # noqa: F401
from .onboarding.readmodel_then import subject_selector_open  # noqa: F401
from .onboarding.readmodel_then import can_set_subject  # noqa: F401
from .onboarding.readmodel_then import editable_fields  # noqa: F401
from .onboarding.readmodel_then import fields_prefilled  # noqa: F401
from .onboarding.readmodel_then import saved_hint  # noqa: F401
from .onboarding.readmodel_then import available_subjects_exclude  # noqa: F401
from .onboarding.readmodel_then import available_subjects_include  # noqa: F401
from .onboarding.readmodel_then import subject_list_contains  # noqa: F401
from .onboarding.readmodel_then import category_contains_subject  # noqa: F401
from .onboarding.readmodel_then import subject_question_count  # noqa: F401
from .onboarding.readmodel_then import custom_subject_added  # noqa: F401
from .onboarding.readmodel_then import subject_date_badge  # noqa: F401
from .onboarding.readmodel_then import subject_level_updated  # noqa: F401
from .onboarding.readmodel_then import navigate_to_step  # noqa: F401
from .onboarding.readmodel_then import category_filter  # noqa: F401

# Admin — aggregate_given
from .admin.aggregate_given import admin_roles_doc  # noqa: F401
from .admin.aggregate_given import user_status_suspended  # noqa: F401
from .admin.aggregate_given import worker_failure_rate  # noqa: F401
from .admin.aggregate_given import many_users  # noqa: F401

# Admin — commands
from .admin.commands import access_admin  # noqa: F401
from .admin.commands import access_settings  # noqa: F401
from .admin.commands import view_dashboard  # noqa: F401
from .admin.commands import search_users  # noqa: F401
from .admin.commands import search_users_empty  # noqa: F401
from .admin.commands import filter_users  # noqa: F401
from .admin.commands import view_user_detail  # noqa: F401
from .admin.commands import adjust_subscription  # noqa: F401
from .admin.commands import suspend_user  # noqa: F401
from .admin.commands import suspend_user_raw  # noqa: F401
from .admin.commands import export_csv  # noqa: F401
from .admin.commands import activate_user  # noqa: F401
from .admin.commands import notify_user  # noqa: F401
from .admin.commands import notify_user_empty  # noqa: F401
from .admin.commands import delete_user  # noqa: F401
from .admin.commands import adjust_role  # noqa: F401
from .admin.commands import adjust_role_by_email  # noqa: F401
from .admin.commands import view_ai_cost  # noqa: F401
from .admin.commands import view_trend_charts  # noqa: F401
from .admin.commands import detect_alerts  # noqa: F401

# Admin — commands
from .admin.commands import admin_ui_actions  # noqa: F401

# Admin — readmodel_then
from .admin.readmodel_then import admin_ui  # noqa: F401
from .admin.readmodel_then import show_dashboard  # noqa: F401
from .admin.readmodel_then import no_settings_menu  # noqa: F401
from .admin.readmodel_then import kpi_fields  # noqa: F401
from .admin.readmodel_then import user_summary  # noqa: F401
from .admin.readmodel_then import all_users_plan  # noqa: F401
from .admin.readmodel_then import user_detail_blocks  # noqa: F401
from .admin.readmodel_then import csv_response  # noqa: F401
from .admin.readmodel_then import no_admin_users  # noqa: F401
from .admin.readmodel_then import trend_data_points  # noqa: F401
from .admin.readmodel_then import ai_model_tokens  # noqa: F401
from .admin.readmodel_then import alert_card  # noqa: F401

# Admin — aggregate_then
from .admin.aggregate_then import user_plan  # noqa: F401
from .admin.aggregate_then import user_status  # noqa: F401
from .admin.aggregate_then import audit_log  # noqa: F401
from .admin.aggregate_then import user_cannot_login  # noqa: F401
from .admin.aggregate_then import user_role  # noqa: F401
from .admin.aggregate_then import email_notify_admins  # noqa: F401
from .admin.aggregate_then import email_user_notification  # noqa: F401

# Admin Finance — aggregate_given
from .admin_finance.aggregate_given import transactions  # noqa: F401
from .admin_finance.aggregate_given import refunds  # noqa: F401
from .admin_finance.aggregate_given import coupons  # noqa: F401

# Admin Finance — commands
from .admin_finance.commands import view_subscription_distribution  # noqa: F401
from .admin_finance.commands import view_transactions  # noqa: F401
from .admin_finance.commands import approve_refund  # noqa: F401
from .admin_finance.commands import reject_refund  # noqa: F401
from .admin_finance.commands import create_coupon  # noqa: F401
from .admin_finance.commands import approve_refund_otp  # noqa: F401
from .admin_finance.commands import finance_ui_actions  # noqa: F401
from .admin_finance.commands import list_refunds  # noqa: F401

# Admin Finance — aggregate_then
from .admin_finance.aggregate_then import refund_status  # noqa: F401
from .admin_finance.aggregate_then import coupon_status  # noqa: F401
from .admin_finance.aggregate_then import subscription_downgraded  # noqa: F401
from .admin_finance.aggregate_then import rejection_email_sent  # noqa: F401

# Admin Finance — readmodel_then
from .admin_finance.readmodel_then import subscription_distribution  # noqa: F401
from .admin_finance.readmodel_then import transaction_list  # noqa: F401
from .admin_finance.readmodel_then import transaction_fields  # noqa: F401
from .admin_finance.readmodel_then import mrr_trend  # noqa: F401
from .admin_finance.readmodel_then import plan_distribution  # noqa: F401
from .admin_finance.readmodel_then import export_finance  # noqa: F401
from .admin_finance.readmodel_then import transaction_filter  # noqa: F401
from .admin_finance.readmodel_then import transaction_detail  # noqa: F401
from .admin_finance.readmodel_then import mrr_chart  # noqa: F401
from .admin_finance.readmodel_then import refunds_coupons  # noqa: F401

# Admin Moderation — aggregate_given
from .admin_moderation.aggregate_given import ai_cooldowns  # noqa: F401
from .admin_moderation.aggregate_given import content_reports  # noqa: F401

# Admin Moderation — commands
from .admin_moderation.commands import view_ai_abuse  # noqa: F401
from .admin_moderation.commands import unlock_cooldown  # noqa: F401
from .admin_moderation.commands import view_report_queue  # noqa: F401
from .admin_moderation.commands import resolve_report  # noqa: F401
from .admin_moderation.commands import click_report_action  # noqa: F401
from .admin_moderation.commands import click_confirm_buttons  # noqa: F401
from .admin_moderation.commands import system_ops_panel  # noqa: F401
from .admin_moderation.commands import moderation_panel_queries  # noqa: F401

# Admin Moderation — aggregate_then
from .admin_moderation.aggregate_then import cooldown_unlocked  # noqa: F401
from .admin_moderation.aggregate_then import report_status  # noqa: F401
from .admin_moderation.aggregate_then import resource_deleted  # noqa: F401
from .admin_moderation.aggregate_then import resource_not_deleted  # noqa: F401
from .admin_moderation.aggregate_then import warn_notification_sent  # noqa: F401

# Admin Moderation — readmodel_then
from .admin_moderation.readmodel_then import cooldown_users  # noqa: F401
from .admin_moderation.readmodel_then import abuse_items  # noqa: F401
from .admin_moderation.readmodel_then import report_count  # noqa: F401
from .admin_moderation.readmodel_then import confirm_dialog  # noqa: F401
from .admin_moderation.readmodel_then import filtered_reports  # noqa: F401

# Admin Settings — aggregate_given
from .admin_settings.aggregate_given import ai_model_routings  # noqa: F401
from .admin_settings.aggregate_given import plan_quotas  # noqa: F401
from .admin_settings.aggregate_given import feature_flags  # noqa: F401
from .admin_settings.aggregate_given import announcement_active_with_id  # noqa: F401
from .admin_settings.aggregate_given import announcement_active_display  # noqa: F401
from .admin_settings.aggregate_given import announcement_inactive  # noqa: F401
from .admin_settings.aggregate_given import announcement_with_id  # noqa: F401
from .admin_settings.aggregate_given import many_audit_logs  # noqa: F401

# Admin Settings — commands
from .admin_settings.commands import update_model_routing  # noqa: F401
from .admin_settings.commands import update_plan_quota  # noqa: F401
from .admin_settings.commands import create_announcement  # noqa: F401
from .admin_settings.commands import create_announcement_admin  # noqa: F401
from .admin_settings.commands import update_feature_flag  # noqa: F401
from .admin_settings.commands import view_audit_logs  # noqa: F401
from .admin_settings.commands import query_public_announcements  # noqa: F401
from .admin_settings.commands import query_active_announcements  # noqa: F401
from .admin_settings.commands import deactivate_announcement  # noqa: F401
from .admin_settings.commands import deactivate_announcement_by_title  # noqa: F401
from .admin_settings.commands import delete_announcement  # noqa: F401
from .admin_settings.commands import create_admin_user  # noqa: F401
from .admin_settings.commands import clear_cache  # noqa: F401
from .admin_settings.commands import reset_ai_limits  # noqa: F401
from .admin_settings.commands import settings_ui_actions  # noqa: F401
from .admin_settings.commands import list_settings  # noqa: F401

# Admin Settings — aggregate_given (feature 24)
from .admin_settings.aggregate_given import announcements_table  # noqa: F401

# Admin Settings — aggregate_then
from .admin_settings.aggregate_then import model_routing_updated  # noqa: F401
from .admin_settings.aggregate_then import plan_quota_updated  # noqa: F401
from .admin_settings.aggregate_then import announcement_status  # noqa: F401
from .admin_settings.aggregate_then import feature_flag_updated  # noqa: F401
from .admin_settings.aggregate_then import announcement_status_by_id  # noqa: F401
from .admin_settings.aggregate_then import announcement_not_exists  # noqa: F401
from .admin_settings.aggregate_then import activation_email_sent  # noqa: F401
from .admin_settings.aggregate_then import announcement_exists_by_title  # noqa: F401
from .admin_settings.aggregate_then import announcement_is_active_field  # noqa: F401

# Admin Settings — readmodel_then
from .admin_settings.readmodel_then import audit_log_fields  # noqa: F401
from .admin_settings.readmodel_then import response_contains_announcement  # noqa: F401
from .admin_settings.readmodel_then import response_not_contains_announcement  # noqa: F401
from .admin_settings.readmodel_then import settings_page_hints  # noqa: F401
from .admin_settings.readmodel_then import admin_table  # noqa: F401
from .admin_settings.readmodel_then import audit_log_ui  # noqa: F401
from .admin_settings.readmodel_then import announcement_count_and_title  # noqa: F401

# Dashboard — aggregate_given
from .dashboard.aggregate_given import user_subjects  # noqa: F401
from .dashboard.aggregate_given import dashboard_ui_state  # noqa: F401

# Dashboard — commands
from .dashboard.commands import view_dashboard  # noqa: F401
from .dashboard.commands import switch_subject  # noqa: F401
from .dashboard.commands import update_profile  # noqa: F401
from .dashboard.commands import dashboard_ui_actions  # noqa: F401

# Dashboard — aggregate_then
from .dashboard.aggregate_then import display_name  # noqa: F401
from .dashboard.aggregate_then import dashboard_state  # noqa: F401

# Dashboard — readmodel_then
from .dashboard.readmodel_then import guidance_prompt  # noqa: F401
from .dashboard.readmodel_then import dashboard_ui  # noqa: F401
from .dashboard.readmodel_then import subject_switcher  # noqa: F401
from .dashboard.readmodel_then import countdown  # noqa: F401
from .dashboard.readmodel_then import components  # noqa: F401

# ECPay — aggregate_given
from .ecpay.aggregate_given import ecpay_config  # noqa: F401
from .ecpay.aggregate_given import current_time  # noqa: F401
from .ecpay.aggregate_given import ecpay_params  # noqa: F401
from .ecpay.aggregate_given import pending_transaction  # noqa: F401
from .ecpay.aggregate_given import transaction_status  # noqa: F401

# ECPay — commands
from .ecpay.commands import create_order_unauthenticated  # noqa: F401
from .ecpay.commands import create_order  # noqa: F401
from .ecpay.commands import calculate_mac  # noqa: F401
from .ecpay.commands import ecpay_callback_invalid  # noqa: F401
from .ecpay.commands import ecpay_callback  # noqa: F401
from .ecpay.commands import ecpay_callback_repeat  # noqa: F401

# ECPay — readmodel_then
from .ecpay.readmodel_then import http_status  # noqa: F401
from .ecpay.readmodel_then import ecpay_form_params  # noqa: F401
from .ecpay.readmodel_then import check_mac_value  # noqa: F401
from .ecpay.readmodel_then import mac_calculation  # noqa: F401
from .ecpay.readmodel_then import callback_response  # noqa: F401

# ECPay — aggregate_then
from .ecpay.aggregate_then import new_transaction  # noqa: F401
from .ecpay.aggregate_then import transaction_updated  # noqa: F401
from .ecpay.aggregate_then import user_subscription as ecpay_user_subscription  # noqa: F401

# Subscription Upgrade — aggregate_given
from .subscription_upgrade.aggregate_given import plan_quota_table  # noqa: F401
from .subscription_upgrade.aggregate_given import pending_order  # noqa: F401
from .subscription_upgrade.aggregate_given import firebase_claims  # noqa: F401
from .subscription_upgrade.aggregate_given import expired_subscription  # noqa: F401
from .subscription_upgrade.aggregate_given import ai_usage  # noqa: F401

# Subscription Upgrade — commands
from .subscription_upgrade.commands import ecpay_success_callback  # noqa: F401
from .subscription_upgrade.commands import process_upgrade  # noqa: F401
from .subscription_upgrade.commands import renew_subscription  # noqa: F401
from .subscription_upgrade.commands import callback_with_exception  # noqa: F401

# Subscription Upgrade — aggregate_then
from .subscription_upgrade.aggregate_then import subscription_updated  # noqa: F401
from .subscription_upgrade.aggregate_then import quota_upgrade  # noqa: F401
from .subscription_upgrade.aggregate_then import advanced_features  # noqa: F401
from .subscription_upgrade.aggregate_then import usage_reset  # noqa: F401
from .subscription_upgrade.aggregate_then import error_handling  # noqa: F401

# Subscription Upgrade — readmodel_then
from .subscription_upgrade.readmodel_then import firebase_claims as sub_firebase_claims  # noqa: F401

# Feedback — aggregate_given
from .feedback.aggregate_given import feedback_records  # noqa: F401
from .feedback.aggregate_given import user_logged_in  # noqa: F401
from .feedback.aggregate_given import user_not_logged_in  # noqa: F401
from .feedback.aggregate_given import recent_feedback  # noqa: F401

# Feedback — commands
from .feedback.commands import click_footer_link  # noqa: F401
from .feedback.commands import submit_api_unauthenticated  # noqa: F401
from .feedback.commands import submit_missing_field  # noqa: F401
from .feedback.commands import submit_long_subject  # noqa: F401
from .feedback.commands import submit_long_content  # noqa: F401
from .feedback.commands import submit_duplicate  # noqa: F401
from .feedback.commands import submit_feedback  # noqa: F401
from .feedback.commands import submit_with_attachments  # noqa: F401
from .feedback.commands import list_feedbacks  # noqa: F401
from .feedback.commands import view_detail  # noqa: F401
from .feedback.commands import admin_access  # noqa: F401
from .feedback.commands import admin_list  # noqa: F401
from .feedback.commands import admin_update  # noqa: F401
from .feedback.commands import admin_stats  # noqa: F401

# Feedback — readmodel_then
from .feedback.readmodel_then import redirect  # noqa: F401
from .feedback.readmodel_then import feedback_form  # noqa: F401
from .feedback.readmodel_then import feedback_created  # noqa: F401
from .feedback.readmodel_then import response_feedback_id  # noqa: F401
from .feedback.readmodel_then import notification_sent  # noqa: F401
from .feedback.readmodel_then import attachment_paths  # noqa: F401
from .feedback.readmodel_then import feedback_list  # noqa: F401
from .feedback.readmodel_then import feedback_fields  # noqa: F401
from .feedback.readmodel_then import no_other_feedback  # noqa: F401

# Feedback — aggregate_then
from .feedback.aggregate_then import feedback_status  # noqa: F401
from .feedback.aggregate_then import feedback_resolved  # noqa: F401

# Anomaly — aggregate_given
from .anomaly.aggregate_given import anomaly_records  # noqa: F401
from .anomaly.aggregate_given import maintenance_tasks  # noqa: F401
from .anomaly.aggregate_given import maintenance_schedule  # noqa: F401

# Anomaly — commands
from .anomaly.commands import access_anomaly_page  # noqa: F401
from .anomaly.commands import create_maintenance_task_params  # noqa: F401
from .anomaly.commands import view_anomaly_list  # noqa: F401
from .anomaly.commands import update_anomaly  # noqa: F401
from .anomaly.commands import create_maintenance_task  # noqa: F401
from .anomaly.commands import update_maintenance_task_status  # noqa: F401
from .anomaly.commands import create_maintenance_schedule  # noqa: F401
from .anomaly.commands import activate_maintenance_mode  # noqa: F401
from .anomaly.commands import detect_schedule_end  # noqa: F401

# Anomaly — aggregate_then
from .anomaly.aggregate_then import anomaly_occurrence_count  # noqa: F401
from .anomaly.aggregate_then import anomaly_classified  # noqa: F401
from .anomaly.aggregate_then import anomaly_status  # noqa: F401
from .anomaly.aggregate_then import new_task_status  # noqa: F401
from .anomaly.aggregate_then import task_status  # noqa: F401
from .anomaly.aggregate_then import notify_technician  # noqa: F401
from .anomaly.aggregate_then import scheduled_notifications  # noqa: F401
from .anomaly.aggregate_then import notify_online_users  # noqa: F401
from .anomaly.aggregate_then import redirect_to_maintenance  # noqa: F401
from .anomaly.aggregate_then import auto_close_maintenance  # noqa: F401

# Anomaly — readmodel_then
from .anomaly.readmodel_then import anomaly_list_fields  # noqa: F401

# Community — aggregate_given
from .community.aggregate_given import exam_scores  # noqa: F401
from .community.aggregate_given import learning_activity  # noqa: F401
from .community.aggregate_given import no_activity  # noqa: F401
from .community.aggregate_given import last_login  # noqa: F401
from .community.aggregate_given import score_decline  # noqa: F401
from .community.aggregate_given import score_stable  # noqa: F401
from .community.aggregate_given import has_activity  # noqa: F401
from .community.aggregate_given import historical_reports  # noqa: F401

# Community — commands
from .community.commands import browse_dashboard  # noqa: F401
from .community.commands import trigger_weekly_report  # noqa: F401
from .community.commands import run_valley_detection  # noqa: F401
from .community.commands import browse_exam_results  # noqa: F401
from .community.commands import view_weekly_reports  # noqa: F401

# Community — readmodel_then
from .community.readmodel_then import no_banner  # noqa: F401
from .community.readmodel_then import has_banner  # noqa: F401
from .community.readmodel_then import banner_format  # noqa: F401
from .community.readmodel_then import no_pii_in_banner  # noqa: F401
from .community.readmodel_then import weekly_report_generated  # noqa: F401
from .community.readmodel_then import report_has_summary  # noqa: F401
from .community.readmodel_then import report_no_ranking  # noqa: F401
from .community.readmodel_then import no_weekly_report  # noqa: F401
from .community.readmodel_then import email_sent  # noqa: F401
from .community.readmodel_then import email_title  # noqa: F401
from .community.readmodel_then import email_tone  # noqa: F401
from .community.readmodel_then import no_callback_email  # noqa: F401
from .community.readmodel_then import weekly_email_sent  # noqa: F401
from .community.readmodel_then import weekly_email_title  # noqa: F401
from .community.readmodel_then import weekly_email_content  # noqa: F401
from .community.readmodel_then import weekly_email_cta  # noqa: F401
from .community.readmodel_then import no_weekly_email  # noqa: F401
from .community.readmodel_then import report_count  # noqa: F401
from .community.readmodel_then import report_fields  # noqa: F401
from .community.readmodel_then import coach_appears  # noqa: F401
from .community.readmodel_then import coach_message  # noqa: F401
from .community.readmodel_then import coach_not_appear  # noqa: F401

# Question Retirement — aggregate_given
from .question_retirement.aggregate_given import ai_gen_service  # noqa: F401
from .question_retirement.aggregate_given import ai_question_answered_correct  # noqa: F401
from .question_retirement.aggregate_given import ai_question_bookmarked  # noqa: F401
from .question_retirement.aggregate_given import ai_question_idle  # noqa: F401
from .question_retirement.aggregate_given import ai_question_in_wrong_book  # noqa: F401
from .question_retirement.aggregate_given import ai_question_no_interaction  # noqa: F401
from .question_retirement.aggregate_given import ai_question_reported  # noqa: F401
from .question_retirement.aggregate_given import ai_question_soft_deleted  # noqa: F401
from .question_retirement.aggregate_given import ai_questions_generated  # noqa: F401
from .question_retirement.aggregate_given import ai_questions_never_answered  # noqa: F401
from .question_retirement.aggregate_given import blind_spot_corrected  # noqa: F401
from .question_retirement.aggregate_given import dangerous_blind_spot  # noqa: F401
from .question_retirement.aggregate_given import expires_at_passed  # noqa: F401
from .question_retirement.aggregate_given import knowledge_node_mastery  # noqa: F401
from .question_retirement.aggregate_given import learning_journey_with_result_date  # noqa: F401
from .question_retirement.aggregate_given import result_date_yesterday  # noqa: F401
from .question_retirement.aggregate_given import result_notification_state  # noqa: F401
from .question_retirement.aggregate_given import sm2_completed  # noqa: F401
from .question_retirement.aggregate_given import sm2_stage  # noqa: F401
from .question_retirement.aggregate_given import subject_question_counts  # noqa: F401

# Question Retirement — commands
from .question_retirement.commands import ai_consent  # noqa: F401
from .question_retirement.commands import ai_generate  # noqa: F401
from .question_retirement.commands import confirm_result  # noqa: F401
from .question_retirement.commands import list_pending  # noqa: F401
from .question_retirement.commands import quality_gate  # noqa: F401
from .question_retirement.commands import result_notification  # noqa: F401
from .question_retirement.commands import retirement_scan  # noqa: F401

# Question Retirement — aggregate_then
from .question_retirement.aggregate_then import available_questions_count  # noqa: F401
from .question_retirement.aggregate_then import hard_delete_result  # noqa: F401
from .question_retirement.aggregate_then import learning_journey_state  # noqa: F401
from .question_retirement.aggregate_then import quality_gate_result  # noqa: F401
from .question_retirement.aggregate_then import question_source_type  # noqa: F401
from .question_retirement.aggregate_then import retirement_state  # noqa: F401

# Question Retirement — readmodel_then
from .question_retirement.readmodel_then import ai_consent_response  # noqa: F401
from .question_retirement.readmodel_then import notification_content  # noqa: F401
from .question_retirement.readmodel_then import onboarding_result_date  # noqa: F401
from .question_retirement.readmodel_then import pending_list  # noqa: F401
from .question_retirement.readmodel_then import retirement_scan_stats  # noqa: F401

# Subscription Trial — commands
from .subscription_trial.commands import start_trial  # noqa: F401

# Subscription Trial — aggregate_then
from .subscription_trial.aggregate_then import trial_status  # noqa: F401

# FUP — commands
from .fup.commands import fup_check  # noqa: F401

# EDU Plan — commands
from .edu_plan.commands import subscribe_edu  # noqa: F401

# Subscription — readmodel_then (08 new)
from .subscription.readmodel_then import plan_comparison  # noqa: F401
from .subscription.readmodel_then import invoice_detail  # noqa: F401

# Subscription — aggregate_then (08 new)
from .subscription.aggregate_then import upload_limit  # noqa: F401
from .subscription.aggregate_then import plan_until_date  # noqa: F401
from .subscription.aggregate_then import feature_access_until  # noqa: F401
from .subscription.aggregate_then import auto_downgrade  # noqa: F401

# Subscription Trial — commands (08 new)
from .subscription_trial.commands import start_ultra_trial  # noqa: F401
from .subscription_trial.commands import trial_expiry_check  # noqa: F401

# Subscription Trial — aggregate_given (08 new)
from .subscription_trial.aggregate_given import has_used_trial  # noqa: F401
from .subscription_trial.aggregate_given import trial_expiring  # noqa: F401
from .subscription_trial.aggregate_given import pre_trial_plan  # noqa: F401
from .subscription_trial.aggregate_given import in_trial  # noqa: F401
from .subscription_trial.aggregate_given import in_trial_remaining  # noqa: F401

# Subscription Trial — aggregate_then (08 new)
from .subscription_trial.aggregate_then import trial_end_date  # noqa: F401
from .subscription_trial.aggregate_then import no_downgrade_trigger  # noqa: F401

# FUP — aggregate_given (08 new)
from .fup.aggregate_given import ai_usage_today  # noqa: F401
from .fup.aggregate_given import consecutive_soft_cap  # noqa: F401

# FUP — commands (08 new)
from .fup.commands import ai_chat_request  # noqa: F401
from .fup.commands import daily_fup_check  # noqa: F401

# FUP — aggregate_then (08 new)
from .fup.aggregate_then import soft_cap_alert  # noqa: F401

# FUP — readmodel_then (08 new)
from .fup.readmodel_then import alert_content  # noqa: F401

# Common Then (08 new)
from .common_then import success_no_block  # noqa: F401

# Subscription Upgrade — aggregate_given (08b new)
from .subscription_upgrade.aggregate_given import csv_import_student  # noqa: F401
from .subscription_upgrade.aggregate_given import edu_student  # noqa: F401
from .subscription_upgrade.aggregate_given import institution_admin_plan  # noqa: F401
from .subscription_upgrade.aggregate_given import edu_student_count  # noqa: F401

# Subscription Upgrade — commands (08b new)
from .subscription_upgrade.commands import remove_from_institution  # noqa: F401
from .subscription_upgrade.commands import institution_cancel  # noqa: F401

# Subscription Upgrade — aggregate_then (08b new)
from .subscription_upgrade.aggregate_then import role_updated  # noqa: F401
from .subscription_upgrade.aggregate_then import quota_exact  # noqa: F401
from .subscription_upgrade.aggregate_then import edu_restrictions  # noqa: F401
from .subscription_upgrade.aggregate_then import batch_downgrade  # noqa: F401

# Pricing — aggregate_given
from .pricing.aggregate_given import plan_definitions  # noqa: F401
from .pricing.aggregate_given import monthly_uploads  # noqa: F401
from .pricing.aggregate_given import never_used_trial  # noqa: F401

# Pricing — commands
from .pricing.commands import browse_pricing_guest  # noqa: F401
from .pricing.commands import browse_pricing_user  # noqa: F401
from .pricing.commands import upload_resource_limit  # noqa: F401
from .pricing.commands import use_coach  # noqa: F401
from .pricing.commands import access_edu_admin  # noqa: F401

# Pricing — readmodel_then
from .pricing.readmodel_then import plans_count  # noqa: F401
from .pricing.readmodel_then import plan_fields  # noqa: F401
from .pricing.readmodel_then import current_plan_marked  # noqa: F401
from .pricing.readmodel_then import ultra_cta  # noqa: F401
from .pricing.readmodel_then import edu_section  # noqa: F401
from .pricing.readmodel_then import upgrade_guidance  # noqa: F401
from .pricing.readmodel_then import ultra_trial_cta  # noqa: F401
from .pricing.readmodel_then import ultra_upgrade_cta  # noqa: F401

# Reverse Engineering — aggregate_given
from .reverse_engineering.aggregate_given import subject_categories  # noqa: F401
from .reverse_engineering.aggregate_given import subjects  # noqa: F401
from .reverse_engineering.aggregate_given import subject_questions  # noqa: F401
from .reverse_engineering.aggregate_given import reverse_engineering_completed  # noqa: F401

# Reverse Engineering — commands
from .reverse_engineering.commands import trigger_reverse_engineering  # noqa: F401
from .reverse_engineering.commands import auto_trigger as re_auto_trigger  # noqa: F401
from .reverse_engineering.commands import trigger_incremental  # noqa: F401
from .reverse_engineering.commands import import_markdown  # noqa: F401

# Reverse Engineering — query
from .reverse_engineering.query import query_knowledge_tree  # noqa: F401
from .reverse_engineering.query import query_node_stats  # noqa: F401
from .reverse_engineering.query import query_unmapped_questions  # noqa: F401
from .reverse_engineering.query import query_quality_report  # noqa: F401
from .reverse_engineering.query import export_markdown  # noqa: F401

# Reverse Engineering — aggregate_then
from .reverse_engineering.aggregate_then import task_created  # noqa: F401
from .reverse_engineering.aggregate_then import knowledge_tree_updated  # noqa: F401
from .reverse_engineering.aggregate_then import incremental_preserve  # noqa: F401

# Reverse Engineering — readmodel_then
from .reverse_engineering.readmodel_then import knowledge_tree_structure  # noqa: F401
from .reverse_engineering.readmodel_then import json_tree_format  # noqa: F401
from .reverse_engineering.readmodel_then import markdown_export  # noqa: F401
from .reverse_engineering.readmodel_then import unmapped_questions  # noqa: F401
from .reverse_engineering.readmodel_then import quality_report  # noqa: F401
from .reverse_engineering.readmodel_then import subscription_locked  # noqa: F401

# Wrong Answer Map — aggregate_given
from .wrong_answer_map.aggregate_given import knowledge_tree_by_table  # noqa: F401
from .wrong_answer_map.aggregate_given import node_answer_records  # noqa: F401
from .wrong_answer_map.aggregate_given import bulk_node_mastery  # noqa: F401
from .wrong_answer_map.aggregate_given import multiple_exams_mastery  # noqa: F401
from .wrong_answer_map.aggregate_given import node_wrong_answers  # noqa: F401
from .wrong_answer_map.aggregate_given import red_nodes_setup  # noqa: F401

# Wrong Answer Map — commands
from .wrong_answer_map.commands import update_node_mastery  # noqa: F401
from .wrong_answer_map.commands import request_ai_suggestion  # noqa: F401

# Wrong Answer Map — query
from .wrong_answer_map.query import query_wrong_answer_map  # noqa: F401
from .wrong_answer_map.query import query_node_wrong_details  # noqa: F401
from .wrong_answer_map.query import export_markdown_mastery  # noqa: F401

# Wrong Answer Map — aggregate_then
from .wrong_answer_map.aggregate_then import mastery_verification  # noqa: F401

# Wrong Answer Map — readmodel_then
from .wrong_answer_map.readmodel_then import color_rules  # noqa: F401
from .wrong_answer_map.readmodel_then import map_response  # noqa: F401
from .wrong_answer_map.readmodel_then import wrong_answer_details  # noqa: F401
from .wrong_answer_map.readmodel_then import time_filter  # noqa: F401
from .wrong_answer_map.readmodel_then import markdown_mastery  # noqa: F401
from .wrong_answer_map.readmodel_then import free_plan_locked  # noqa: F401
from .wrong_answer_map.readmodel_then import ai_suggestion_response  # noqa: F401

# Difficulty Progression — aggregate_given
from .difficulty_progression.aggregate_given import knowledge_tree_with_difficulty  # noqa: F401
from .difficulty_progression.aggregate_given import practice_state  # noqa: F401
from .difficulty_progression.aggregate_given import trigger_conditions  # noqa: F401
from .difficulty_progression.aggregate_given import adaptive_practice  # noqa: F401

# Difficulty Progression — commands
from .difficulty_progression.commands import calculate_strategy  # noqa: F401

# Difficulty Progression — query
from .difficulty_progression.query import learning_trail  # noqa: F401

# Difficulty Progression — readmodel_then
from .difficulty_progression.readmodel_then import strategy_response  # noqa: F401
from .difficulty_progression.readmodel_then import adaptive_response  # noqa: F401

# Knowledge Merge — aggregate_given
from .knowledge_merge.aggregate_given import no_knowledge_tree  # noqa: F401
from .knowledge_merge.aggregate_given import reverse_engineering_nodes  # noqa: F401
from .knowledge_merge.aggregate_given import existing_knowledge_tree  # noqa: F401
from .knowledge_merge.aggregate_given import document_extraction  # noqa: F401
from .knowledge_merge.aggregate_given import merge_conflicts  # noqa: F401
from .knowledge_merge.aggregate_given import merge_state  # noqa: F401
from .knowledge_merge.aggregate_given import node_setup  # noqa: F401
from .knowledge_merge.aggregate_given import unified_knowledge_tree  # noqa: F401
from .knowledge_merge.aggregate_given import uploaded_documents  # noqa: F401

# Knowledge Merge — commands
from .knowledge_merge.commands import trigger_merge  # noqa: F401
from .knowledge_merge.commands import resolve_conflict  # noqa: F401
from .knowledge_merge.commands import trigger_chunk_remap  # noqa: F401
from .knowledge_merge.commands import unified_extract  # noqa: F401

# Knowledge Merge — query
from .knowledge_merge.query import merge_conflicts_list  # noqa: F401
from .knowledge_merge.query import merge_history  # noqa: F401
from .knowledge_merge.query import query_node_detail  # noqa: F401
from .knowledge_merge.query import query_wrong_answer_map_feature29  # noqa: F401
# query_knowledge_tree reuses reverse_engineering step
# Note: export_markdown_source reuses reverse_engineering/query/export_markdown step

# Knowledge Merge — aggregate_then
from .knowledge_merge.aggregate_then import conflict_resolved  # noqa: F401
from .knowledge_merge.aggregate_then import mastery_preserved  # noqa: F401
from .knowledge_merge.aggregate_then import chunks_mapped  # noqa: F401
from .knowledge_merge.aggregate_then import depth_one_constraints  # noqa: F401

# Knowledge Merge — readmodel_then
from .knowledge_merge.readmodel_then import unified_tree  # noqa: F401
from .knowledge_merge.readmodel_then import dashboard_depth_one  # noqa: F401
from .knowledge_merge.readmodel_then import merge_result  # noqa: F401
from .knowledge_merge.readmodel_then import semantic_similarity  # noqa: F401
from .knowledge_merge.readmodel_then import conflict_records  # noqa: F401
from .knowledge_merge.readmodel_then import node_metadata  # noqa: F401
from .knowledge_merge.readmodel_then import merge_history_response  # noqa: F401
from .knowledge_merge.readmodel_then import unified_tree_query  # noqa: F401
from .knowledge_merge.readmodel_then import markdown_source  # noqa: F401
from .knowledge_merge.readmodel_then import downstream_updates  # noqa: F401

# Prompt Template — aggregate_given
from .prompt_template.aggregate_given import prompt_templates  # noqa: F401

# Prompt Template — commands
from .prompt_template.commands import list_templates  # noqa: F401
from .prompt_template.commands import get_template  # noqa: F401
from .prompt_template.commands import create_template  # noqa: F401
from .prompt_template.commands import update_template  # noqa: F401
from .prompt_template.commands import version_commands  # noqa: F401
from .prompt_template.commands import ab_test_commands  # noqa: F401
from .prompt_template.commands import internal_api  # noqa: F401

# Prompt Template — aggregate_then
from .prompt_template.aggregate_then import template_state  # noqa: F401
from .prompt_template.aggregate_then import ab_test_state  # noqa: F401

# Prompt Template — readmodel_then
from .prompt_template.readmodel_then import template_response  # noqa: F401
from .prompt_template.readmodel_then import internal_api_response  # noqa: F401

# AI Gen Service (Feature 04a) — 所有 step 已合併至 exam 子領域。
# ai_gen 子領域保留但不再 import（避免 AmbiguousStep 衝突）。
from .exam.readmodel_then import historical_mode  # noqa: F401

# Tenant Security (Feature 31) — aggregate_given
from .tenant_security.aggregate_given import active_tenants  # noqa: F401
from .tenant_security.aggregate_given import tenant_student  # noqa: F401
from .tenant_security.aggregate_given import tenant_logged_in  # noqa: F401
from .tenant_security.aggregate_given import b2c_logged_in  # noqa: F401
from .tenant_security.aggregate_given import tenant_chunks  # noqa: F401
from .tenant_security.aggregate_given import tenant_exam_answers  # noqa: F401
from .tenant_security.aggregate_given import old_jwt  # noqa: F401
from .tenant_security.aggregate_given import logged_in_user  # noqa: F401
from .tenant_security.aggregate_given import tenant_decommissioned  # noqa: F401
from .tenant_security.aggregate_given import test_resources  # noqa: F401

# Tenant Security (Feature 31) — commands
from .tenant_security.commands import upload_resource  # noqa: F401
from .tenant_security.commands import query_resource_chunks  # noqa: F401
from .tenant_security.commands import query_answers  # noqa: F401
from .tenant_security.commands import login_tenant  # noqa: F401
from .tenant_security.commands import access_resources_legacy  # noqa: F401
from .tenant_security.commands import submit_url  # noqa: F401
from .tenant_security.commands import purge_tenant_script  # noqa: F401
from .tenant_security.commands import purge_target_public_b2c  # noqa: F401
from .tenant_security.commands import bdd_env_check  # noqa: F401
from .tenant_security.commands import after_scenario_truncate  # noqa: F401

# Tenant Security (Feature 31) — aggregate_then
from .tenant_security.aggregate_then import tenant_id_in_resources  # noqa: F401
from .tenant_security.aggregate_then import tenant_id_in_chunks  # noqa: F401
from .tenant_security.aggregate_then import chunk_isolation  # noqa: F401
from .tenant_security.aggregate_then import answer_isolation  # noqa: F401
from .tenant_security.aggregate_then import purge_dry_run  # noqa: F401

# Tenant Security (Feature 31) — readmodel_then
from .tenant_security.readmodel_then import jwt_tenant_id  # noqa: F401
from .tenant_security.readmodel_then import legacy_compat  # noqa: F401
from .tenant_security.readmodel_then import ssrf_rejection  # noqa: F401
from .tenant_security.readmodel_then import bdd_env_isolation  # noqa: F401
from .tenant_security.readmodel_then import guc_null_safe  # noqa: F401

# Tenant Security (PRD-033) — undefined steps fix
from .tenant_security.aggregate_given import no_guc_set  # noqa: F401
from .tenant_security.aggregate_given import null_tenant_rows  # noqa: F401
from .tenant_security.aggregate_then import migration_061_backfill  # noqa: F401
from .tenant_security.commands import alembic_upgrade_061  # noqa: F401
from .tenant_security.commands import query_resources_no_guc  # noqa: F401

# Confidence Calibration (Feature 20) — aggregate_given
from .confidence_calibration.aggregate_given import exam_with_answers  # noqa: F401

# Confidence Calibration (Feature 20) — commands
from .confidence_calibration.commands import answer_with_confidence  # noqa: F401

# Confidence Calibration (Feature 20) — aggregate_then
from .confidence_calibration.aggregate_then import answer_state  # noqa: F401

# Confidence Calibration (Feature 20) — readmodel_then
from .confidence_calibration.readmodel_then import confidence_analysis  # noqa: F401

# Pomodoro (Feature 21) — 純前端功能，spec 移至 project/features/21-番茄鐘學習節奏.feature
# step 檔於 2026-04-27 整批刪除（@frontend 規範，見 docs/bdd/tag-conventions.md）

# Practice (Feature 32) — aggregate_given
from .practice.aggregate_given import knowledge_nodes  # noqa: F401
from .practice.aggregate_given import practice_questions  # noqa: F401

# Practice (Feature 32) — commands
from .practice.commands import practice_actions  # noqa: F401

# Practice (Feature 32) — readmodel_then
from .practice.readmodel_then import practice_results  # noqa: F401

# Epic 3 Node Mastery Pipeline
from .practice.aggregate_given import node_mastery_setup  # noqa: F401
from .practice.aggregate_given import root_mastery_setup  # noqa: F401
from .practice.aggregate_given import practice_v3_setup  # noqa: F401
from .practice.commands import practice_correct_answer  # noqa: F401
from .practice.commands import add_new_nodes  # noqa: F401
from .practice.commands import practice_v3_answer  # noqa: F401
from .practice.aggregate_then import node_mastery_assertions  # noqa: F401
from .practice.aggregate_then import root_mastery_diluted  # noqa: F401
from .practice.aggregate_then import practice_v3_assertions  # noqa: F401

# Pomodoro readmodel_then 同樣已隨 step 子領域刪除

# Account Settings (Feature 22) — aggregate_given
from .account_settings.aggregate_given import user_setup  # noqa: F401

# Account Settings (Feature 22) — commands
from .account_settings.commands import account_actions  # noqa: F401

# Account Settings (Feature 22) — aggregate_then
from .account_settings.aggregate_then import account_state  # noqa: F401

# Account Settings (Feature 22) — readmodel_then
from .account_settings.readmodel_then import account_response  # noqa: F401

# MCP Context Server (Feature 30) — aggregate_given
from .mcp_context.aggregate_given import setup_knowledge_nodes  # noqa: F401

# MCP Context Server (Feature 30) — commands
from .mcp_context.commands import call_context_server  # noqa: F401

# MCP Context Server (Feature 30) — readmodel_then
from .mcp_context.readmodel_then import verify_context_response  # noqa: F401

# MCP Recommendation Server (Feature 31) — aggregate_given
from .mcp_recommendation.aggregate_given import setup_mastery_data  # noqa: F401

# MCP Recommendation Server (Feature 31) — commands
from .mcp_recommendation.commands import call_recommendation_server  # noqa: F401

# MCP Recommendation Server (Feature 31) — readmodel_then
from .mcp_recommendation.readmodel_then import verify_recommendation_response  # noqa: F401

# Exam Import — Database Integration (Feature 32 Phase 2)
from .exam_import.database_import import step_clear_historical_data  # noqa: F401
from .exam_import.database_import import step_existing_import  # noqa: F401
from .exam_import.database_import import step_import_questions  # noqa: F401
from .exam_import.database_import import step_call_import_api  # noqa: F401
from .exam_import.database_import import step_reimport_exam  # noqa: F401
from .exam_import.database_import import step_verify_exam_count  # noqa: F401
from .exam_import.database_import import step_verify_question_count  # noqa: F401
from .exam_import.database_import import step_verify_foreign_keys  # noqa: F401
from .exam_import.database_import import step_verify_question_content  # noqa: F401
from .exam_import.database_import import step_verify_import_success  # noqa: F401
from .exam_import.database_import import step_verify_duplicate_update  # noqa: F401
from .exam_import.database_import import step_verify_skip_duplicate  # noqa: F401
from .exam_import.database_import import step_verify_query_endpoint  # noqa: F401
from .exam_import.database_import import step_verify_questions_endpoint  # noqa: F401
from .exam_import.database_import import step_verify_validation_endpoint  # noqa: F401
from .exam_import.database_import import step_verify_timestamp  # noqa: F401
from .exam_import.database_import import step_verify_validation_model  # noqa: F401
from .exam_import.database_import import step_verify_bulk_performance  # noqa: F401
from .exam_import.database_import import step_verify_acid_compliance  # noqa: F401
# Feature 33 — Async import lifecycle
from .exam_import import async_import as _exam_import_async_import  # noqa: F401
# Cost Monitor (Feature 33) — aggregate_given
from .cost_monitor.aggregate_given import budget_config as cm_budget_config  # noqa: F401
from .cost_monitor.aggregate_given import current_usage as cm_current_usage  # noqa: F401
from .cost_monitor.aggregate_given import misc_given as cm_misc_given  # noqa: F401
from .cost_monitor.aggregate_given import scenario_extras as cm_scenario_extras  # noqa: F401

# Cost Monitor (Feature 33) — commands
from .cost_monitor.commands import view_endpoints as cm_view_endpoints  # noqa: F401
from .cost_monitor.commands import budget_mutations as cm_budget_mutations  # noqa: F401
from .cost_monitor.commands import internal_actions as cm_internal_actions  # noqa: F401

# Cost Monitor (Feature 33) — readmodel_then
from .cost_monitor.readmodel_then import response_fields as cm_response_fields  # noqa: F401
from .cost_monitor.readmodel_then import misc_then as cm_misc_then  # noqa: F401

# Cost Monitor (Feature 33) — aggregate_then
from .cost_monitor.aggregate_then import db_assertions as cm_db_assertions  # noqa: F401

# Common — error code (shared across features)
from .common_then import error_code as common_error_code  # noqa: F401

# Mindmap Upgrade (Feature 34) — aggregate_given
from .mindmap_upgrade.aggregate_given import (  # noqa: F401
    setup_nodes_and_chunks as mu_setup,
    rerank_schema_setup as mu_rerank_setup,
    llm_integration_setup as mu_llm_setup,
)

# Mindmap Upgrade (Feature 34) — commands
from .mindmap_upgrade.commands import (  # noqa: F401
    direct_service_calls as mu_commands,
    rerank_schema_commands as mu_rerank_commands,
    llm_integration_commands as mu_llm_commands,
)

# Mindmap Upgrade (Feature 34) — aggregate_then
from .mindmap_upgrade.aggregate_then import (  # noqa: F401
    assertions as mu_assertions,
    rerank_schema_assertions as mu_rerank_assertions,
    llm_integration_assertions as mu_llm_assertions,
)

# Coverage retrofit (Feature 35, ISS-015)
from .coverage.commands import retrofit_calls  # noqa: F401

# Canvas (PRD-046)
from .canvas.aggregate_given import fixtures as canvas_fixtures  # noqa: F401
from .canvas.commands import canvas_queries  # noqa: F401
from .canvas.commands import analytics_calls  # noqa: F401
from .canvas.readmodel_then import canvas_assertions  # noqa: F401

# Bloom Analysis (Feature 18) — 題目分類與考試趨勢分析
from .bloom_analysis.aggregate_given import (  # noqa: F401
    background as ba_background,
    exam_setup as ba_exam_setup,
    exam_completed as ba_exam_completed,
    admin_import as ba_admin_import,
)
from .bloom_analysis.query import bloom_distribution as ba_query_dist  # noqa: F401
from .bloom_analysis.commands import (  # noqa: F401
    submit_config as ba_submit_config,
    admin_actions as ba_admin_actions,
    view_result as ba_view_result,
)
from .bloom_analysis.readmodel_then import (  # noqa: F401
    bloom_distribution_then as ba_dist_then,
    exam_response_then as ba_exam_response_then,
    result_bloom_then as ba_result_then,
    admin_then as ba_admin_then,
)

# Cloud Tasks Pipeline Split (Worker B+ epic, 2026-04-29)
from .tasks.commands import process_resource_task as _tasks_process_resource  # noqa: F401

# F19 Interleaved Practice
from .interleaved.aggregate_given import exam_setup as _il_exam_setup  # noqa: F401
from .interleaved.commands import interleaved_actions as _il_actions  # noqa: F401
from .interleaved.readmodel_then import interleaved_assertions as _il_assertions  # noqa: F401

# F23 考古題題庫管理
from .exam_bank import exam_bank_steps as _f23_exam_bank  # noqa: F401

# F35/F36 — Subject & Resource Hard Delete (P0)
from .subject.aggregate_given import subject_with_children as _f35_subj_given  # noqa: F401
from .subject.commands import hard_delete_api as _f35_subj_cmd  # noqa: F401
from .subject.aggregate_then import db_assertions as _f35_subj_then  # noqa: F401
from .subject.readmodel_then import preview_response as _f35_subj_readmodel  # noqa: F401
from .resource.aggregate_given import owned_resource_with_chunks as _f36_res_given  # noqa: F401
from .resource.commands import hard_delete_api as _f36_res_cmd  # noqa: F401
from .resource.aggregate_then import hard_delete_db as _f36_res_then  # noqa: F401
from .resource.aggregate_then import hidden_resource_db as _f36_hidden_then  # noqa: F401

# Orphan Scaffold Fill (#2 AI 補洞鷹架) — Sprint 11
from .orphan_scaffold.aggregate_given import orphan_node_setup  # noqa: F401
from .orphan_scaffold.commands import orphan_scaffold_api  # noqa: F401
from .orphan_scaffold.readmodel_then import response_assertions  # noqa: F401

# Orphan Coach (#9 AI 蘇格拉底教練對話) — Sprint 12
from .orphan_coach.aggregate_given import orphan_nodes  # noqa: F401
from .orphan_coach.commands import api_calls as orphan_coach_api  # noqa: F401
from .orphan_coach.readmodel_then import response_body as orphan_coach_response  # noqa: F401
