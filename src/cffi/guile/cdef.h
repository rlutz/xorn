typedef struct scm_unused_struct { char scm_unused_field; } *SCM;

typedef enum { SCM_F_DYNWIND_REWINDABLE } scm_t_dynwind_flags;
typedef enum { SCM_F_WIND_EXPLICITLY } scm_t_wind_flags;

typedef void (*scm_t_pointer_finalizer) (void *);
typedef void *scm_t_subr;

typedef int32_t scm_t_int32;
typedef uint32_t scm_t_uint32;
typedef int64_t scm_t_int64;
typedef uint64_t scm_t_uint64;

const SCM SCM_BOOL_T;
const SCM SCM_BOOL_F;
const SCM SCM_EOL;
const SCM SCM_UNSPECIFIED;

extern "Python" void *_lookup_cb(void *);
extern "Python" void *_define_cb(void *);
extern "Python" void *_load_cb(void *);
extern "Python" void *_eval_string_cb(void *);
extern "Python" void *_scm2py_call_cb(void *);
extern "Python" void *_py2scm_call_cb(void *);
extern "Python" SCM _py2scm_call_gsubr(SCM args);

void free(void *ptr);

SCM scm_apply (SCM proc, SCM arg1, SCM args);
SCM scm_c_define (const char *name, SCM val);
SCM scm_c_lookup (const char *name);
SCM scm_c_make_gsubr (const char *name,
		      int req, int opt, int rst, scm_t_subr fcn);
SCM scm_car (SCM x);
SCM scm_cdr (SCM x);
SCM scm_cons (SCM x, SCM y);
SCM scm_current_module (void);
void scm_dynwind_begin (scm_t_dynwind_flags);
void scm_dynwind_end (void);
void scm_dynwind_unwind_handler (void (*func) (void *), void *data,
				 scm_t_wind_flags);
void scm_error (SCM key, const char *subr, const char *message,
		SCM args, SCM rest);
SCM scm_eval (SCM exp, SCM module);
SCM scm_eval_string (SCM string);
SCM scm_frame_procedure_name (SCM frame);
SCM scm_from_double (double val);
SCM scm_from_int64 (scm_t_int64 x);
SCM scm_from_locale_string (const char *str);
SCM scm_from_locale_stringn (const char *str, size_t len);
SCM scm_from_utf8_string (const char *str);
SCM scm_from_utf8_stringn (const char *str, size_t len);
SCM scm_from_utf8_symbol (const char *str);
int scm_is_bool (SCM x);
int scm_is_eq (SCM x, SCM y);
int scm_is_exact_integer (SCM val);
int scm_is_null (SCM x);
int scm_is_pair (SCM x);
int scm_is_real (SCM val);
int scm_is_string (SCM x);
SCM scm_length (SCM x);
SCM scm_list_1 (SCM e1);
SCM scm_list_2 (SCM e1, SCM e2);
SCM scm_list_p (SCM x);
SCM scm_make_stack (SCM obj, SCM args);
SCM scm_procedure_name (SCM proc);
SCM scm_procedure_p (SCM obj);
SCM scm_simple_format (SCM port, SCM message, SCM args);
SCM scm_stack_ref (SCM stack, SCM i);
SCM scm_symbol_to_string (SCM s);
SCM scm_throw (SCM key, SCM args);
int scm_to_bool (SCM x);
double scm_to_double (SCM val);
scm_t_int64 scm_to_int64 (SCM x);
scm_t_uint64 scm_to_uint64 (SCM x);
char *scm_to_utf8_stringn (SCM str, size_t *lenp);
SCM scm_variable_ref (SCM var);
void *scm_with_guile (void *(*func)(void *), void *data);
void *scm_without_guile (void *(*func)(void *), void *data);
