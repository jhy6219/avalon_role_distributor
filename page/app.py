import dash
from dash import html, dcc, Input, Output, State, ctx, ALL, MATCH
import dash_bootstrap_components as dbc
import random
from datetime import datetime
import pandas as pd
import sys
import os

current_file_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(current_file_path)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(grandparent_dir)
from ftn.generate_msg import distributor

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 결과를 저장할 전역 변수
stored_results = None
result_timestamp = None
selected_roles = []  # 선택된 역할을 저장할 변수
default_domain = "@naver.com"
stored_df = None  # DataFrame을 저장할 전역 변수

app.layout = dbc.Container([
    html.H1("👼아발론 역할 분배기😈", 
            className="my-4 text-center",
            style={
            "textShadow": "2px 2px 4px rgba(0, 0, 0, 0.1)"
            }
    ),

    dbc.Row([
        dbc.Col([
            dbc.Checklist(
                options=[
                    {"label": "🕵️‍♂️ 퍼시발 포함", "value": "percival"},
                    {"label": "🧙‍♀️ 모르가나 포함", "value": "morgana"}
                ],
                id="role-toggles",
                inline=True,
                switch=True,
                className="mb-3"
            ),
        ], width={"size": 6}, className="text-center")
    ], justify="center"),

    dbc.Row([
        dbc.Col([
            html.Div(id="input-container", children=[]),
        ], width=10)
    ], justify="center"),

    dbc.Row([
        dbc.Col([
            dbc.Button(
                "+", 
                id="add-person", 
                outline=True,
                color="primary", 
                className="rounded-circle",
                style={
                    "width": "38px",
                    "height": "38px",
                    "fontSize": "20px",
                    "padding": "0",
                    "boxShadow": "0 1px 2px rgba(0,0,0,0.05)",
                    "marginTop": "10px",
                    "marginBottom": "10px"
                }
            ),
        ], width={"size": 6}, className="text-center")
    ], justify="center"),

    dbc.Row([
        dbc.Col([
            dbc.Button("이메일 보내기", id="send-email", color="success", className="mt-3 mb-3"),
            html.Div(id="email-status", className="mt-3"),
            dbc.Button("결과 확인하기", id="show-results", color="info", className="mt-3 mb-3", style={"display": "none"}),
            html.Div(id="results-area", className="mt-3")
        ], className="text-center")
    ], justify="center"),

    # 확인 모달
    dbc.Modal([
        dbc.ModalHeader("결과 확인"),
        dbc.ModalBody("결과를 확인하시겠습니까?"),
        dbc.ModalFooter([
            dbc.Button("취소", id="cancel-modal", className="ms-auto", color="secondary"),
            dbc.Button("확인", id="confirm-modal", className="ms-2", color="primary"),
        ]),
    ], id="confirm-modal-div", is_open=False),

], fluid=True)


# 콜백: 입력 필드 추가
@app.callback(
    Output("input-container", "children"),
    Input("add-person", "n_clicks"),
    State("input-container", "children"),
    prevent_initial_call=True
)
def add_input(n, children):
    if children is None:
        children = []
    index = len(children)
    new_inputs = dbc.Row([
        dbc.Col(
            html.Span(f"{index + 1}.", 
                     style={
                         "fontSize": "1.2em", 
                         "fontWeight": "bold",
                         "color": "#6c757d",
                         "marginRight": "-5px"
                     }),
            width="auto",
            className="pe-0"
        ),
        dbc.Col(
            dbc.Input(
                placeholder="이름", 
                type="text", 
                id={'type': 'name', 'index': index},
                style={
                    "borderRadius": "10px",
                    "border": "1px solid #e9ecef",
                    "transition": "border-color 0.3s ease, box-shadow 0.3s ease",
                    "boxShadow": "0 1px 2px rgba(0,0,0,0.05)"
                }
            ), 
            width=3,
            className="ps-2"
        ),
        dbc.Col([
            dbc.InputGroup([
                dbc.Input(
                    placeholder="이메일", 
                    type="text", 
                    id={'type': 'email', 'index': index},
                    style={
                        "borderRadius": "10px 0 0 10px",
                        "border": "1px solid #e9ecef",
                        "borderRight": "none",
                        "transition": "border-color 0.3s ease, box-shadow 0.3s ease",
                        "boxShadow": "0 1px 2px rgba(0,0,0,0.05)"
                    }
                ),
                dbc.Input(
                    placeholder="@도메인.com",
                    type="text",
                    id={'type': 'domain', 'index': index},
                    value=default_domain,
                    style={
                        "width": "150px",
                        "borderRadius": "0 10px 10px 0",
                        "border": "1px solid #e9ecef",
                        "borderLeft": "none",
                        "transition": "border-color 0.3s ease, box-shadow 0.3s ease",
                        "boxShadow": "0 1px 2px rgba(0,0,0,0.05)"
                    }
                )
            ])
        ], width=7),
        dbc.Col(
            dbc.Button(
                "✕", 
                id={'type': 'remove', 'index': index},
                color="danger",
                size="sm",
                className="rounded-circle",
                style={
                    "width": "32px", 
                    "height": "32px",
                    "boxShadow": "0 1px 2px rgba(0,0,0,0.1)"
                }
            ),
            width="auto",
            className="ps-2"
        )
    ], className="mb-3 align-items-center", id={'type': 'row', 'index': index})
    children.append(new_inputs)
    return children


# 콜백: 행 삭제
@app.callback(
    Output({'type': 'row', 'index': MATCH}, 'style'),
    Input({'type': 'remove', 'index': MATCH}, 'n_clicks'),
    prevent_initial_call=True
)
def remove_input(n_clicks):
    if n_clicks:
        return {'display': 'none'}
    return dash.no_update


# 콜백: 역할 선택 처리
@app.callback(
    Output("role-toggles", "value"),
    Input("role-toggles", "value"),
    prevent_initial_call=True
)
def handle_role_selection(values):
    global selected_roles
    selected_roles = values if values else []
    return values


# 콜백: 이메일 보내기 처리
@app.callback(
    [Output("email-status", "children"),
     Output("show-results", "style")],
    Input("send-email", "n_clicks"),
    [State({'type': 'row', 'index': ALL}, 'style'),
     State({'type': 'name', 'index': ALL}, 'value'),
     State({'type': 'email', 'index': ALL}, 'value'),
     State({'type': 'domain', 'index': ALL}, 'value'),
     State("role-toggles", "value")],
    prevent_initial_call=True
)
def handle_email(n_clicks, styles, names, emails, domains, selected_roles):
    global stored_results, result_timestamp, stored_df
    
    selected_roles = selected_roles if selected_roles else []
    is_persival=("percival" in selected_roles)
    is_morigana=("morgana" in selected_roles)

    # 기본 유효성 검사
    valid_data = [(i+1, n.strip(), e.strip() + (d or default_domain))
                  for i, (n, e, d, s) in enumerate(zip(names, emails, domains, styles))
                  if s is None and n and n.strip() and e and e.strip()]
    
    if not valid_data:
        return dbc.Alert("이름과 이메일이 입력되지 않았습니다!", color="danger"), {"display": "none"}
    
    # DataFrame 생성
    df = pd.DataFrame(valid_data, columns=['player_ids', 'name', 'email'])
    
    # 이름과 이메일 개수 체크
    if len(df['name'].unique()) != len(df):
        return dbc.Alert(f"이름({len(df['name'].unique())}개)과 입력 행({len(df)}개)의 개수가 일치하지 않습니다!", 
                        color="warning"), {"display": "none"}

    # 중복 체크
    dup_names = df[df['name'].duplicated()]['name'].unique()
    dup_emails = df[df['email'].duplicated()]['email'].unique()
    
    if len(dup_names) > 0 or len(dup_emails) > 0:
        error_msg = []
        if len(dup_names) > 0: error_msg.append(f"❗중복된 이름: {', '.join(dup_names)}")
        if len(dup_emails) > 0: error_msg.append(f"❗중복된 이메일: {', '.join(dup_emails)}")
        return dbc.Alert("\n".join(error_msg), color="warning"), {"display": "none"}

    if len(dup_names) > 0 or len(dup_emails) > 0:
        error_msg = []
        if len(dup_names) > 0: error_msg.append(f"❗중복된 이름: {', '.join(dup_names)}")
        if len(dup_emails) > 0: error_msg.append(f"❗중복된 이메일: {', '.join(dup_emails)}")
        return dbc.Alert("\n".join(error_msg), color="warning"), {"display": "none"}
    
    if len(df) > 10 or len(df) < 5:
        return dbc.Alert("인원 수가 5~10명이어야 합니다!", color="warning"), {"display": "none"}

    # print(df)
    # print(selected_roles)
    stored_df = df  # DataFrame 저장
    distributor_result = distributor(
            stored_df.player_ids, 
            is_persival= is_persival,
            is_morigana= is_morigana
        )

    # 결과 생성
    selected_roles = selected_roles if selected_roles else []
    results = []
    for _, row in df.iterrows():
        role = (" (퍼시벌)" if "percival" in selected_roles and random.random() < 0.3 else
               " (모르가나)" if "morgana" in selected_roles and random.random() < 0.3 else "")
        result = random.choice(["합격 🎉", "불합격 😢", "보류 🤔", "통과 ✅", "실패 ❌"]) + role
        results.append((row['name'], row['email'], result))
    
    stored_results = results
    result_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return dbc.Alert("이메일이 발송되었습니다!", color="success"), {"display": "block"}


# 콜백: 모달 표시/숨김
@app.callback(
    Output("confirm-modal-div", "is_open"),
    [Input("show-results", "n_clicks"),
     Input("cancel-modal", "n_clicks"),
     Input("confirm-modal", "n_clicks")],
    [State("confirm-modal-div", "is_open")],
    prevent_initial_call=True
)
def toggle_modal(show_n_clicks, cancel_n_clicks, confirm_n_clicks, is_open):
    if ctx.triggered_id == "show-results":
        return True
    return False


# 콜백: 결과 표시
@app.callback(
    Output("results-area", "children"),
    Input("confirm-modal", "n_clicks"),
    prevent_initial_call=True
)
def show_results(n_clicks):
    if stored_results is None:
        return dbc.Alert("아직 이메일을 보내지 않았습니다!", color="warning")
    
    return [
        dbc.Alert(f"{result_timestamp} 기준 결과:", color="info", className="mb-3"),
        *[dbc.Alert(f"{name} ({email}): {result}", color="info", className="mb-2") 
          for name, email, result in stored_results]
    ]


# 초기 한 쌍의 입력 필드 표시
@app.callback(
    Output("input-container", "children", allow_duplicate=True),
    Input("input-container", "children"),
    prevent_initial_call="initial_duplicate"
)
def initialize_inputs(children):
    if not children:
        return [
            dbc.Row([
                dbc.Col(
                    html.Span("1.", 
                             style={
                                 "fontSize": "1.2em", 
                                 "fontWeight": "bold",
                                 "color": "#6c757d",
                                 "marginRight": "-5px"
                             }),
                    width="auto",
                    className="pe-0"
                ),
                dbc.Col(
                    dbc.Input(
                        placeholder="이름", 
                        type="text", 
                        id={'type': 'name', 'index': 0},
                        style={
                            "borderRadius": "10px",
                            "border": "1px solid #e9ecef",
                            "transition": "border-color 0.3s ease, box-shadow 0.3s ease",
                            "boxShadow": "0 1px 2px rgba(0,0,0,0.05)"
                        }
                    ), 
                    width=3,
                    className="ps-2"
                ),
                dbc.Col([
                    dbc.InputGroup([
                        dbc.Input(
                            placeholder="이메일", 
                            type="text", 
                            id={'type': 'email', 'index': 0},
                            style={
                                "borderRadius": "10px 0 0 10px",
                                "border": "1px solid #e9ecef",
                                "borderRight": "none",
                                "transition": "border-color 0.3s ease, box-shadow 0.3s ease",
                                "boxShadow": "0 1px 2px rgba(0,0,0,0.05)"
                            }
                        ),
                        dbc.Input(
                            placeholder="@도메인.com",
                            type="text",
                            id={'type': 'domain', 'index': 0},
                            value=default_domain,
                            style={
                                "width": "150px",
                                "borderRadius": "0 10px 10px 0",
                                "border": "1px solid #e9ecef",
                                "borderLeft": "none",
                                "transition": "border-color 0.3s ease, box-shadow 0.3s ease",
                                "boxShadow": "0 1px 2px rgba(0,0,0,0.05)"
                            }
                        )
                    ])
                ], width=7),
                dbc.Col(
                    dbc.Button(
                        "✕", 
                        id={'type': 'remove', 'index': 0},
                        color="danger",
                        size="sm",
                        className="rounded-circle",
                        style={
                            "width": "32px", 
                            "height": "32px",
                            "boxShadow": "0 1px 2px rgba(0,0,0,0.1)"
                        }
                    ),
                    width="auto",
                    className="ps-2"
                )
            ], className="mb-3 align-items-center", id={'type': 'row', 'index': 0})
        ]
    return dash.no_update


if __name__ == "__main__":
    app.run(debug=True)
