/** @file

  A brief file description

  @section license License

  Licensed to the Apache Software Foundation (ASF) under one
  or more contributor license agreements.  See the NOTICE file
  distributed with this work for additional information
  regarding copyright ownership.  The ASF licenses this file
  to you under the Apache License, Version 2.0 (the
  "License"); you may not use this file except in compliance
  with the License.  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
 */

/****************************************************************************

  StatPages.h


 ****************************************************************************/

#pragma once
#include "I_EventSystem.h"

#include "HTTP.h"

//              SPECIAL URLs
//
//
// 1. Access from Browsers
//
//    By special URLS:
//
//      http://{module}/component/sub-component/request-type?arguments
//
//    Note how the hostname is the module to be queried with "{}" surrounding.
//
//    Running Example:
//
//      http://{http}/groups/dump?comp.compilers
//
// 2. What sort of things should be available?
//
//    A. The type of data should default to HTML or match the
//       extension type e.g.:
//
//         http://{http}/groups/use_graph.gif?august
//
//    B. Each protocol/subsystem should have their own information.
//       For example

#define STAT_PAGE_SUCCESS STAT_PAGES_EVENTS_START + 0
#define STAT_PAGE_FAILURE STAT_PAGES_EVENTS_START + 1

using StatPagesFunc = Action *(*)(Continuation *, HTTPHdr *);

struct StatPageData {
  char *data = nullptr;
  char *type = nullptr;
  int length = 0;

  StatPageData() {}
  StatPageData(char *adata) : data(adata) { length = strlen(adata); }
  StatPageData(char *adata, int alength) : data(adata), length(alength) {}
};

struct StatPagesManager {
  void init();

  void register_http(const char *hostname, StatPagesFunc func);

  // Private
  Action *handle_http(Continuation *cont, HTTPHdr *header);
  bool is_stat_page(URL *url);
  bool is_cache_inspector_page(URL *url);
  int m_enabled;
  ink_mutex stat_pages_mutex;
};

extern StatPagesManager statPagesManager;

// Stole Pete's code for formatting the page and slapped it here
//   for easy reuse
class BaseStatPagesHandler : public Continuation
{
public:
  BaseStatPagesHandler(ProxyMutex *amutex) : Continuation(amutex), response(nullptr), response_size(0), response_length(0){};
  ~BaseStatPagesHandler() override { resp_clear(); };

protected:
  void resp_clear();
  void resp_add(const char *fmt, ...);
  void resp_add_sep();
  void resp_begin(const char *title);
  void resp_end();
  void resp_begin_numbered();
  void resp_end_numbered();
  void resp_begin_unnumbered();
  void resp_end_unnumbered();
  void resp_begin_item();
  void resp_end_item();
  void resp_begin_table(int border, int columns, int percent);
  void resp_end_table();
  void resp_begin_row();
  void resp_end_row();
  void resp_begin_column(int percent = -1, const char *align = nullptr);
  void resp_end_column();

  char *response;
  int response_size;
  int response_length;
};
