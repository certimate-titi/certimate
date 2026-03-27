# behave 在載入 step 模組時，globals 可能缺少 __name__，導致相對匯入失敗
if "__name__" not in globals():
    __name__ = "tests.features.steps"
if "__package__" not in globals():
    __package__ = "tests.features.steps"

# Common Then
from .common_then import success  # noqa: F401
from .common_then import failure  # noqa: F401
from .common_then import failure_with_reason  # noqa: F401
from .common_then import error_message  # noqa: F401
from .common_then import failure_with_error  # noqa: F401

# Auth — aggregate_given
from .auth.aggregate_given import users  # noqa: F401
from .auth.aggregate_given import user_auth_provider  # noqa: F401
from .auth.aggregate_given import user_has_journey  # noqa: F401
from .auth.aggregate_given import user_no_journey  # noqa: F401
from .auth.aggregate_given import user_role  # noqa: F401
from .auth.aggregate_given import user_subscription_and_role  # noqa: F401
from .auth.aggregate_given import user_subscription  # noqa: F401
from .auth.aggregate_given import user_verified  # noqa: F401

# Auth — commands
from .auth.commands import check_password_strength  # noqa: F401
from .auth.commands import forgot_password  # noqa: F401
from .auth.commands import google_sso  # noqa: F401
from .auth.commands import login  # noqa: F401
from .auth.commands import login_by_email  # noqa: F401
from .auth.commands import register  # noqa: F401
from .auth.commands import register_no_terms  # noqa: F401
from .auth.commands import user_action  # noqa: F401

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

# Auth — readmodel_then
from .auth.readmodel_then import jwt_token  # noqa: F401
from .auth.readmodel_then import login_no_error  # noqa: F401
from .auth.readmodel_then import navbar_not_shows  # noqa: F401
from .auth.readmodel_then import navbar_shows  # noqa: F401
from .auth.readmodel_then import password_strength  # noqa: F401
from .auth.readmodel_then import redirect_to  # noqa: F401
from .auth.readmodel_then import response_contains  # noqa: F401
from .auth.readmodel_then import user_info  # noqa: F401

# Resource — aggregate_given
from .resource.aggregate_given import user_subject  # noqa: F401

# Resource — commands
from .resource.commands import upload_file  # noqa: F401
from .resource.commands import upload_file_with_size  # noqa: F401
from .resource.commands import upload_image  # noqa: F401
from .resource.commands import upload_pdf  # noqa: F401
from .resource.commands import submit_youtube  # noqa: F401
from .resource.commands import upload_missing_params  # noqa: F401

# Resource — readmodel_then
from .resource.readmodel_then import resource_status  # noqa: F401
from .resource.readmodel_then import processing_engine  # noqa: F401
from .resource.readmodel_then import implicit_consent  # noqa: F401
from .resource.readmodel_then import resource_type  # noqa: F401

# Knowledge Map — aggregate_given
from .knowledge_map.aggregate_given import knowledge_node_data  # noqa: F401
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

# Knowledge Map — commands
from .knowledge_map.commands import ai_coach_input  # noqa: F401
from .knowledge_map.commands import ai_coach_input_locked  # noqa: F401
from .knowledge_map.commands import answer_questions_correctly  # noqa: F401
from .knowledge_map.commands import click_knowledge_node  # noqa: F401
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

# Knowledge Map — aggregate_then
from .knowledge_map.aggregate_then import knowledge_tree_created  # noqa: F401
from .knowledge_map.aggregate_then import knowledge_tree_with_timestamps  # noqa: F401
from .knowledge_map.aggregate_then import resource_status_updated  # noqa: F401
from .knowledge_map.aggregate_then import tree_hierarchy  # noqa: F401
from .knowledge_map.aggregate_then import leaf_node_source  # noqa: F401
from .knowledge_map.aggregate_then import coach_quota_remaining  # noqa: F401

# Knowledge Map — readmodel_then
from .knowledge_map.readmodel_then import achievement_animation  # noqa: F401
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

# Exam — aggregate_given
from .exam.aggregate_given import resources  # noqa: F401
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

# Exam — query
from .exam.query import select_subject_filter  # noqa: F401

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
from .exam.readmodel_then import stage2_output  # noqa: F401
from .exam.readmodel_then import stage3_output  # noqa: F401
from .exam.readmodel_then import stage4_output  # noqa: F401
from .exam.readmodel_then import prompt_template_then  # noqa: F401
from .exam.readmodel_then import retry_then  # noqa: F401

# Mock Exam — aggregate_given
from .mock_exam.aggregate_given import exams  # noqa: F401
from .mock_exam.aggregate_given import questions  # noqa: F401
from .mock_exam.aggregate_given import saved_answers  # noqa: F401
from .mock_exam.aggregate_given import exam_started  # noqa: F401

# Mock Exam — commands
from .mock_exam.commands import start_exam  # noqa: F401
from .mock_exam.commands import select_answer  # noqa: F401
from .mock_exam.commands import mark_review  # noqa: F401
from .mock_exam.commands import submit_exam  # noqa: F401
from .mock_exam.commands import resume_exam  # noqa: F401
from .mock_exam.commands import fill_in_answer  # noqa: F401

# Mock Exam — aggregate_then
from .mock_exam.aggregate_then import exam_status  # noqa: F401
from .mock_exam.aggregate_then import exam_started_at  # noqa: F401
from .mock_exam.aggregate_then import answer_saved  # noqa: F401
from .mock_exam.aggregate_then import review_marked  # noqa: F401

# Mock Exam — readmodel_then
from .mock_exam.readmodel_then import resume_answer  # noqa: F401

# Exam Result — aggregate_given
from .exam_result.aggregate_given import history_exams  # noqa: F401
from .exam_result.aggregate_given import node_stats  # noqa: F401

# Exam Result — commands
from .exam_result.commands import view_result  # noqa: F401
from .exam_result.commands import view_node_analysis  # noqa: F401

# Exam Result — readmodel_then
from .exam_result.readmodel_then import result_fields  # noqa: F401
from .exam_result.readmodel_then import node_analysis  # noqa: F401

# Wrong Answer — aggregate_given
from .wrong_answer.aggregate_given import exam_wrong_records  # noqa: F401
from .wrong_answer.aggregate_given import user_profile  # noqa: F401
from .wrong_answer.aggregate_given import historical_wrong  # noqa: F401
from .wrong_answer.aggregate_given import cooldown_history  # noqa: F401

# Wrong Answer — commands
from .wrong_answer.commands import filter_by_subject  # noqa: F401
from .wrong_answer.commands import view_wrong_answers  # noqa: F401
from .wrong_answer.commands import ai_coach  # noqa: F401
from .wrong_answer.commands import ai_coach_generic  # noqa: F401

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

# Subscription — aggregate_given
from .subscription.aggregate_given import invoices  # noqa: F401

# Subscription — commands
from .subscription.commands import subscribe  # noqa: F401
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

# B2B — commands
from .b2b.commands import access_admin  # noqa: F401

# B2B — readmodel_then
from .b2b.readmodel_then import institution_name  # noqa: F401

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

# Onboarding — aggregate_then
from .onboarding.aggregate_then import journeys_created  # noqa: F401
from .onboarding.aggregate_then import onboarding_completed  # noqa: F401
from .onboarding.aggregate_then import journey_created  # noqa: F401
from .onboarding.aggregate_then import switcher_added  # noqa: F401
from .onboarding.aggregate_then import journey_unaffected  # noqa: F401
from .onboarding.aggregate_then import journey_archived  # noqa: F401
from .onboarding.aggregate_then import switcher_removed  # noqa: F401

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

# Admin — aggregate_given
from .admin.aggregate_given import admin_roles_doc  # noqa: F401

# Admin — commands
from .admin.commands import access_admin  # noqa: F401
from .admin.commands import access_settings  # noqa: F401
from .admin.commands import view_dashboard  # noqa: F401
from .admin.commands import search_users  # noqa: F401
from .admin.commands import filter_users  # noqa: F401
from .admin.commands import view_user_detail  # noqa: F401
from .admin.commands import adjust_subscription  # noqa: F401
from .admin.commands import suspend_user  # noqa: F401
from .admin.commands import suspend_user_raw  # noqa: F401
from .admin.commands import export_csv  # noqa: F401

# Admin — readmodel_then
from .admin.readmodel_then import show_dashboard  # noqa: F401
from .admin.readmodel_then import no_settings_menu  # noqa: F401
from .admin.readmodel_then import kpi_fields  # noqa: F401
from .admin.readmodel_then import user_summary  # noqa: F401
from .admin.readmodel_then import all_users_plan  # noqa: F401
from .admin.readmodel_then import user_detail_blocks  # noqa: F401
from .admin.readmodel_then import csv_response  # noqa: F401

# Admin — aggregate_then
from .admin.aggregate_then import user_plan  # noqa: F401
from .admin.aggregate_then import user_status  # noqa: F401
from .admin.aggregate_then import audit_log  # noqa: F401
from .admin.aggregate_then import user_cannot_login  # noqa: F401

# Admin Finance — aggregate_given
from .admin_finance.aggregate_given import transactions  # noqa: F401
from .admin_finance.aggregate_given import refunds  # noqa: F401

# Admin Finance — commands
from .admin_finance.commands import view_subscription_distribution  # noqa: F401
from .admin_finance.commands import view_transactions  # noqa: F401
from .admin_finance.commands import approve_refund  # noqa: F401
from .admin_finance.commands import reject_refund  # noqa: F401
from .admin_finance.commands import create_coupon  # noqa: F401

# Admin Finance — aggregate_then
from .admin_finance.aggregate_then import refund_status  # noqa: F401
from .admin_finance.aggregate_then import coupon_status  # noqa: F401

# Admin Finance — readmodel_then
from .admin_finance.readmodel_then import subscription_distribution  # noqa: F401
from .admin_finance.readmodel_then import transaction_list  # noqa: F401

# Admin Moderation — aggregate_given
from .admin_moderation.aggregate_given import ai_cooldowns  # noqa: F401
from .admin_moderation.aggregate_given import content_reports  # noqa: F401

# Admin Moderation — commands
from .admin_moderation.commands import view_ai_abuse  # noqa: F401
from .admin_moderation.commands import unlock_cooldown  # noqa: F401
from .admin_moderation.commands import view_report_queue  # noqa: F401
from .admin_moderation.commands import resolve_report  # noqa: F401

# Admin Moderation — aggregate_then
from .admin_moderation.aggregate_then import cooldown_unlocked  # noqa: F401
from .admin_moderation.aggregate_then import report_status  # noqa: F401

# Admin Moderation — readmodel_then
from .admin_moderation.readmodel_then import cooldown_users  # noqa: F401
from .admin_moderation.readmodel_then import report_count  # noqa: F401

# Admin Settings — aggregate_given
from .admin_settings.aggregate_given import ai_model_routings  # noqa: F401
from .admin_settings.aggregate_given import plan_quotas  # noqa: F401
from .admin_settings.aggregate_given import feature_flags  # noqa: F401

# Admin Settings — commands
from .admin_settings.commands import update_model_routing  # noqa: F401
from .admin_settings.commands import update_plan_quota  # noqa: F401
from .admin_settings.commands import create_announcement  # noqa: F401
from .admin_settings.commands import update_feature_flag  # noqa: F401
from .admin_settings.commands import view_audit_logs  # noqa: F401

# Admin Settings — aggregate_then
from .admin_settings.aggregate_then import model_routing_updated  # noqa: F401
from .admin_settings.aggregate_then import plan_quota_updated  # noqa: F401
from .admin_settings.aggregate_then import announcement_status  # noqa: F401
from .admin_settings.aggregate_then import feature_flag_updated  # noqa: F401

# Admin Settings — readmodel_then
from .admin_settings.readmodel_then import audit_log_fields  # noqa: F401

# Dashboard — aggregate_given
from .dashboard.aggregate_given import user_subjects  # noqa: F401

# Dashboard — commands
from .dashboard.commands import view_dashboard  # noqa: F401
from .dashboard.commands import switch_subject  # noqa: F401
from .dashboard.commands import update_profile  # noqa: F401

# Dashboard — aggregate_then
from .dashboard.aggregate_then import display_name  # noqa: F401

# Dashboard — readmodel_then
from .dashboard.readmodel_then import guidance_prompt  # noqa: F401
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

# Community — commands
from .community.commands import browse_dashboard  # noqa: F401
from .community.commands import trigger_weekly_report  # noqa: F401
from .community.commands import run_valley_detection  # noqa: F401
from .community.commands import browse_exam_results  # noqa: F401

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
from .community.readmodel_then import coach_appears  # noqa: F401
from .community.readmodel_then import coach_message  # noqa: F401
from .community.readmodel_then import coach_not_appear  # noqa: F401
