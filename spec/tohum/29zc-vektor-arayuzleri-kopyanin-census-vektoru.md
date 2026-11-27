# Vektör Arayüzleri: Kopyanın `census` Vektörü

Tarih: 2026-11-24 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: kopya hedefin K0 sayımı okunurken ve `census_copy` grubu okunurken
Çapa: `seed/bootstrap/vectors/vectors.json` (`census_copy`); `seed/bootstrap/local/census_copy.json`

---

**`census_copy`** (Aşama 1 çıkışı; operatör kararı, 2026-11-20, `29za`; E744). Kopya `Okan-wqm/snowball-rehearsal-copy`,
`base_sha` `4f479013a42f4b750e0784cc2500bd17d932af1a`; birimler hakemin `setup/summary.json`'undaki
`targets[kind=copy].unit_candidates`. Kopyanın kendi ESLint'i (9.39.4; Node 20.11.0, npm 10.2.4, sürümler koşudan
okundu; `npm ci --ignore-scripts`) birimlerin git'te izlenen 262 dosyasının her birine soruldu; hangisini lint ettiğine
ESLint karar verir (yok sayılmayan ve bir yapılandırmanın uyduğu dosya, `--print-config`'in `undefined` demediği): 258
dosya, JSON dosyaları dahil; `.html` ve `.css` değil. Etkin kural önem derecesi "warn", "error", 1 ya da 2 olandır
(dizide ilk öğe); "off" ve 0 değildir; başka bir değer türetmeyi durdurur. Birimin kümesi lint edilen dosyalarının etkin
kurallarının birleşimidir: `platform/libs/outbox` 127, `libs/storage` 130, `web/modules/messaging-module` 182,
`web/modules/hr-module` 103 kural. Kopyanın kümesi birleşimdir (`29za` sonu, E744): 186 kural (101'i dört birimde, 25'i
üçünde, 3'ü ikisinde, 57'si birinde); her vakanın amacı birimlerini adlandırır. 56 kural yalnız `web/modules/*`
birimlerinde etkindir, 54'ü yalnız `web/modules/messaging-module`'de: `29za:15-17`'nin koşulu onların vakalarını bu
birimlerde ister. Komut `census`'unkidir (`29za:24-25`): `python -m cases.build produce eslint <kural>`, değişmiş
girdisi `no-such-rule`. Türetme `seed/bootstrap/local/census_copy.py`, kaydı `census_copy.json` (sha256
`33a0ca77bd6f8039fd8889869eb889775e9a5b0142e2a21edf8a56f61e00d6b0`): birim kümeleri, dosya başına karar ve hash'ler, her
ayrı kanonik `rules` nesnesi seçenekleriyle bir kez (15 nesne); ham çıktı checkout'un mutlak yolunu taşır, `rules`
nesnesi taşımaz ve yeniden üretilen odur.

Vaka adı kuralın adıdır; `@` düşer, `/` ve `-` `_` olur: `nx_enforce_module_boundaries`
`typescript_eslint_adjacent_overload_signatures` `typescript_eslint_await_thenable` `typescript_eslint_ban_ts_comment`
`typescript_eslint_explicit_function_return_type` `typescript_eslint_no_array_constructor`
`typescript_eslint_no_array_delete` `typescript_eslint_no_base_to_string` `typescript_eslint_no_duplicate_enum_values`
`typescript_eslint_no_duplicate_type_constituents` `typescript_eslint_no_dynamic_delete`
`typescript_eslint_no_empty_function` `typescript_eslint_no_empty_interface` `typescript_eslint_no_empty_object_type`
`typescript_eslint_no_explicit_any` `typescript_eslint_no_extra_non_null_assertion`
`typescript_eslint_no_extraneous_class` `typescript_eslint_no_floating_promises` `typescript_eslint_no_for_in_array`
`typescript_eslint_no_implied_eval` `typescript_eslint_no_inferrable_types` `typescript_eslint_no_invalid_void_type`
`typescript_eslint_no_misused_new` `typescript_eslint_no_misused_promises` `typescript_eslint_no_namespace`
`typescript_eslint_no_non_null_asserted_nullish_coalescing` `typescript_eslint_no_non_null_asserted_optional_chain`
`typescript_eslint_no_non_null_assertion` `typescript_eslint_no_redundant_type_constituents`
`typescript_eslint_no_require_imports` `typescript_eslint_no_this_alias`
`typescript_eslint_no_unnecessary_type_assertion` `typescript_eslint_no_unnecessary_type_constraint`
`typescript_eslint_no_unsafe_argument` `typescript_eslint_no_unsafe_assignment` `typescript_eslint_no_unsafe_call`
`typescript_eslint_no_unsafe_declaration_merging` `typescript_eslint_no_unsafe_enum_comparison`
`typescript_eslint_no_unsafe_function_type` `typescript_eslint_no_unsafe_member_access`
`typescript_eslint_no_unsafe_return` `typescript_eslint_no_unsafe_unary_minus` `typescript_eslint_no_unused_expressions`
`typescript_eslint_no_unused_vars` `typescript_eslint_no_useless_constructor`
`typescript_eslint_no_wrapper_object_types` `typescript_eslint_only_throw_error` `typescript_eslint_prefer_as_const`
`typescript_eslint_prefer_literal_enum_member` `typescript_eslint_prefer_namespace_keyword`
`typescript_eslint_prefer_promise_reject_errors` `typescript_eslint_require_await`
`typescript_eslint_restrict_plus_operands` `typescript_eslint_restrict_template_expressions`
`typescript_eslint_triple_slash_reference` `typescript_eslint_unbound_method` `typescript_eslint_unified_signatures`
`aquaculture_no_bare_graphql_query_string` `aquaculture_no_bare_tenant_query_key` `aquaculture_no_claude_sdk_raw_call`
`aquaculture_no_direct_event_publish` `aquaculture_no_high_cardinality_metric_label`
`aquaculture_no_unpinned_ssrf_fetch` `aquaculture_no_unsandboxed_html_frame` `constructor_super` `for_direction`
`getter_return` `import_order` `jsx_a11y_alt_text` `jsx_a11y_anchor_has_content` `jsx_a11y_anchor_is_valid`
`jsx_a11y_aria_activedescendant_has_tabindex` `jsx_a11y_aria_props` `jsx_a11y_aria_proptypes` `jsx_a11y_aria_role`
`jsx_a11y_aria_unsupported_elements` `jsx_a11y_autocomplete_valid` `jsx_a11y_click_events_have_key_events`
`jsx_a11y_heading_has_content` `jsx_a11y_html_has_lang` `jsx_a11y_iframe_has_title` `jsx_a11y_img_redundant_alt`
`jsx_a11y_interactive_supports_focus` `jsx_a11y_label_has_associated_control` `jsx_a11y_media_has_caption`
`jsx_a11y_mouse_events_have_key_events` `jsx_a11y_no_access_key` `jsx_a11y_no_autofocus`
`jsx_a11y_no_distracting_elements` `jsx_a11y_no_interactive_element_to_noninteractive_role`
`jsx_a11y_no_noninteractive_element_interactions` `jsx_a11y_no_noninteractive_element_to_interactive_role`
`jsx_a11y_no_noninteractive_tabindex` `jsx_a11y_no_redundant_roles` `jsx_a11y_no_static_element_interactions`
`jsx_a11y_role_has_required_aria_props` `jsx_a11y_role_supports_aria_props` `jsx_a11y_scope`
`jsx_a11y_tabindex_no_positive` `no_alert` `no_async_promise_executor` `no_case_declarations` `no_class_assign`
`no_compare_neg_zero` `no_cond_assign` `no_console` `no_const_assign` `no_constant_binary_expression`
`no_constant_condition` `no_control_regex` `no_debugger` `no_delete_var` `no_dupe_args` `no_dupe_class_members`
`no_dupe_else_if` `no_dupe_keys` `no_duplicate_case` `no_empty` `no_empty_character_class` `no_empty_pattern`
`no_empty_static_block` `no_ex_assign` `no_extra_boolean_cast` `no_fallthrough` `no_func_assign` `no_global_assign`
`no_import_assign` `no_invalid_regexp` `no_irregular_whitespace` `no_loss_of_precision` `no_misleading_character_class`
`no_new_native_nonconstructor` `no_nonoctal_decimal_escape` `no_obj_calls` `no_octal` `no_prototype_builtins`
`no_redeclare` `no_regex_spaces` `no_restricted_imports` `no_restricted_syntax` `no_self_assign` `no_setter_return`
`no_shadow_restricted_names` `no_sparse_arrays` `no_this_before_super` `no_undef` `no_unexpected_multiline`
`no_unreachable` `no_unsafe_finally` `no_unsafe_negation` `no_unsafe_optional_chaining` `no_unused_labels`
`no_unused_private_class_members` `no_unused_vars` `no_useless_backreference` `no_useless_catch` `no_useless_escape`
`no_var` `no_with` `prefer_const` `prefer_rest_params` `prefer_spread` `react_hooks_exhaustive_deps`
`react_hooks_rules_of_hooks` `react_display_name` `react_jsx_key` `react_jsx_no_comment_textnodes`
`react_jsx_no_duplicate_props` `react_jsx_no_target_blank` `react_jsx_no_undef` `react_jsx_uses_react`
`react_jsx_uses_vars` `react_no_children_prop` `react_no_danger_with_children` `react_no_deprecated`
`react_no_direct_mutation_state` `react_no_find_dom_node` `react_no_is_mounted` `react_no_render_return_value`
`react_no_string_refs` `react_no_unescaped_entities` `react_no_unknown_property` `react_require_render_return`
`require_yield` `use_isnan` `valid_typeof`.
