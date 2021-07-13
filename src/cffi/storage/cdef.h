void free(void *ptr);  /* export free(3) for freeing returned object lists */
int memcmp(const void *s1, const void *s2, size_t n);

extern "Python" void _incref_cb(void *ptr);
extern "Python" void _decref_cb(void *ptr);

typedef enum {
	xorn_obtype_none,	/* object does not exist */
	xornsch_obtype_arc,
	xornsch_obtype_box,
	xornsch_obtype_circle,
	xornsch_obtype_component,
	xornsch_obtype_line,
	xornsch_obtype_net,
	xornsch_obtype_path,
	xornsch_obtype_picture,
	xornsch_obtype_text,
} xorn_obtype_t;

typedef enum {
	xorn_attst_na,
	/* None of the selected objects has this attribute.
	   Don't show this attribute in the property editor. */
	xorn_attst_consistent,
	/* All selected objects have the same value of this attribute.
	   Show this value for this attribute in the property editor. */
	xorn_attst_inconsistent,
	/* There are different values of this attribute between the
	   selected objects.  Show this attribute in the property
	   editor, but don't show a value. */
} xorn_attst_t;

typedef enum {
	xorn_error_invalid_argument,
	xorn_error_out_of_memory,
	xorn_error_revision_not_transient,
	xorn_error_object_doesnt_exist,
	xorn_error_invalid_object_data,
	xorn_error_parent_doesnt_exist,
	xorn_error_invalid_parent,
	xorn_error_invalid_existing_child,
	xorn_error_successor_doesnt_exist,
	xorn_error_successor_not_sibling,
} xorn_error_t;

/* opaque types */
typedef struct xorn_revision *xorn_revision_t;
typedef struct xorn_object *xorn_object_t;
typedef struct xorn_selection *xorn_selection_t;

/* revision functions */

xorn_revision_t xorn_new_revision(xorn_revision_t rev);
bool xorn_revision_is_transient(xorn_revision_t rev);
void xorn_finalize_revision(xorn_revision_t rev);
void xorn_free_revision(xorn_revision_t rev);

/* object functions */

bool xorn_object_exists_in_revision(
	xorn_revision_t rev, xorn_object_t ob);
xorn_obtype_t xorn_get_object_type(
	xorn_revision_t rev, xorn_object_t ob);
const void *xorn_get_object_data(
	xorn_revision_t rev, xorn_object_t ob, xorn_obtype_t type);
int xorn_get_object_location(
	xorn_revision_t rev, xorn_object_t ob,
	xorn_object_t *attached_to_return,
	unsigned int *position_return);

int xorn_get_objects(
	xorn_revision_t rev,
	xorn_object_t **objects_return, size_t *count_return);
int xorn_get_objects_attached_to(
	xorn_revision_t rev, xorn_object_t ob,
	xorn_object_t **objects_return, size_t *count_return);
int xorn_get_selected_objects(
	xorn_revision_t rev, xorn_selection_t sel,
	xorn_object_t **objects_return, size_t *count_return);
int xorn_get_added_objects(
	xorn_revision_t from_rev, xorn_revision_t to_rev,
	xorn_object_t **objects_return, size_t *count_return);
int xorn_get_removed_objects(
	xorn_revision_t from_rev, xorn_revision_t to_rev,
	xorn_object_t **objects_return, size_t *count_return);
int xorn_get_modified_objects(
	xorn_revision_t from_rev, xorn_revision_t to_rev,
	xorn_object_t **objects_return, size_t *count_return);

/* selection functions */

xorn_selection_t xorn_select_none();
xorn_selection_t xorn_select_object(
	xorn_object_t ob);
xorn_selection_t xorn_select_attached_to(
	xorn_revision_t rev, xorn_object_t ob);
xorn_selection_t xorn_select_all(
	xorn_revision_t rev);
xorn_selection_t xorn_select_all_except(
	xorn_revision_t rev, xorn_selection_t sel);
xorn_selection_t xorn_select_including(
	xorn_selection_t sel, xorn_object_t ob);
xorn_selection_t xorn_select_excluding(
	xorn_selection_t sel, xorn_object_t ob);
xorn_selection_t xorn_select_union(
	xorn_selection_t sel0, xorn_selection_t sel1);
xorn_selection_t xorn_select_intersection(
	xorn_selection_t sel0, xorn_selection_t sel1);
xorn_selection_t xorn_select_difference(
	xorn_selection_t sel0, xorn_selection_t sel1);

bool xorn_selection_is_empty(
	xorn_revision_t rev, xorn_selection_t sel);
bool xorn_object_is_selected(
	xorn_revision_t rev, xorn_selection_t sel, xorn_object_t ob);
void xorn_free_selection(
	xorn_selection_t sel);

/* manipulation functions */

xorn_object_t xorn_add_object(xorn_revision_t rev,
			      xorn_obtype_t type, const void *data,
			      xorn_error_t *err);
int xorn_set_object_data(xorn_revision_t rev, xorn_object_t ob,
			 xorn_obtype_t type, const void *data,
			 xorn_error_t *err);
int xorn_relocate_object(xorn_revision_t rev, xorn_object_t ob,
			 xorn_object_t attach_to, xorn_object_t insert_before,
			 xorn_error_t *err);
int xorn_delete_object(xorn_revision_t rev, xorn_object_t ob,
		       xorn_error_t *err);
int xorn_delete_selected_objects(xorn_revision_t rev, xorn_selection_t sel,
				 xorn_error_t *err);

xorn_object_t xorn_copy_object(xorn_revision_t dest,
			       xorn_revision_t src, xorn_object_t ob,
			       xorn_error_t *err);
xorn_selection_t xorn_copy_objects(xorn_revision_t dest,
				   xorn_revision_t src, xorn_selection_t sel,
				   xorn_error_t *err);

/* object data definition */

struct xorn_string {
	const char *s;
	size_t len;
};

struct xorn_double2d {
	double x, y;
};

struct xorn_pointer {
	void *ptr;
	void (*incref)(void *ptr);
	void (*decref)(void *ptr);
};

struct xornsch_line_attr {
	double width;
	int cap_style;
	int dash_style;
	double dash_length;
	double dash_space;
};

struct xornsch_fill_attr {
	int type;
	double width;
	int angle0;
	double pitch0;
	int angle1;
	double pitch1;
};

struct xornsch_arc {
	struct xorn_double2d pos;
	double radius;
	int startangle;
	int sweepangle;
	int color;
	struct xornsch_line_attr line;
};

struct xornsch_box {
	struct xorn_double2d pos;
	struct xorn_double2d size;
	int color;
	struct xornsch_line_attr line;
	struct xornsch_fill_attr fill;
};

struct xornsch_circle {
	struct xorn_double2d pos;
	double radius;
	int color;
	struct xornsch_line_attr line;
	struct xornsch_fill_attr fill;
};

struct xornsch_component {
	struct xorn_double2d pos;
	bool selectable;
	int angle;
	bool mirror;
	struct xorn_pointer symbol;
};

struct xornsch_line {
	struct xorn_double2d pos;
	struct xorn_double2d size;
	int color;
	struct xornsch_line_attr line;
};

struct xornsch_net {
	struct xorn_double2d pos;
	struct xorn_double2d size;
	int color;
	bool is_bus;
	bool is_pin;
	bool is_inverted;
};

struct xornsch_path {
	struct xorn_string pathdata;
	int color;
	struct xornsch_line_attr line;
	struct xornsch_fill_attr fill;
};

struct xornsch_picture {
	struct xorn_double2d pos;
	struct xorn_double2d size;
	int angle;
	bool mirror;
	struct xorn_pointer pixmap;
};

struct xornsch_text {
	struct xorn_double2d pos;
	int color;
	int text_size;
	bool visibility;
	int show_name_value;
	int angle;
	int alignment;
	struct xorn_string text;
};

/* object type-specific functions */

const struct xornsch_arc *xornsch_get_arc_data(xorn_revision_t rev,
					       xorn_object_t ob);
xorn_object_t xornsch_add_arc(xorn_revision_t rev,
			      const struct xornsch_arc *data,
			      xorn_error_t *err);
int xornsch_set_arc_data(xorn_revision_t rev, xorn_object_t ob,
			 const struct xornsch_arc *data,
			 xorn_error_t *err);

const struct xornsch_box *xornsch_get_box_data(xorn_revision_t rev,
					       xorn_object_t ob);
xorn_object_t xornsch_add_box(xorn_revision_t rev,
			      const struct xornsch_box *data,
			      xorn_error_t *err);
int xornsch_set_box_data(xorn_revision_t rev, xorn_object_t ob,
			 const struct xornsch_box *data,
			 xorn_error_t *err);

const struct xornsch_circle *xornsch_get_circle_data(xorn_revision_t rev,
						     xorn_object_t ob);
xorn_object_t xornsch_add_circle(xorn_revision_t rev,
				 const struct xornsch_circle *data,
				 xorn_error_t *err);
int xornsch_set_circle_data(xorn_revision_t rev, xorn_object_t ob,
			    const struct xornsch_circle *data,
			    xorn_error_t *err);

const struct xornsch_component *xornsch_get_component_data(xorn_revision_t
							   rev,
							   xorn_object_t
							   ob);
xorn_object_t xornsch_add_component(xorn_revision_t rev,
				    const struct xornsch_component *data,
				    xorn_error_t *err);
int xornsch_set_component_data(xorn_revision_t rev, xorn_object_t ob,
			       const struct xornsch_component *data,
			       xorn_error_t *err);

const struct xornsch_line *xornsch_get_line_data(xorn_revision_t rev,
						 xorn_object_t ob);
xorn_object_t xornsch_add_line(xorn_revision_t rev,
			       const struct xornsch_line *data,
			       xorn_error_t *err);
int xornsch_set_line_data(xorn_revision_t rev, xorn_object_t ob,
			  const struct xornsch_line *data,
			  xorn_error_t *err);

const struct xornsch_net *xornsch_get_net_data(xorn_revision_t rev,
					       xorn_object_t ob);
xorn_object_t xornsch_add_net(xorn_revision_t rev,
			      const struct xornsch_net *data,
			      xorn_error_t *err);
int xornsch_set_net_data(xorn_revision_t rev, xorn_object_t ob,
			 const struct xornsch_net *data,
			 xorn_error_t *err);

const struct xornsch_path *xornsch_get_path_data(xorn_revision_t rev,
						 xorn_object_t ob);
xorn_object_t xornsch_add_path(xorn_revision_t rev,
			       const struct xornsch_path *data,
			       xorn_error_t *err);
int xornsch_set_path_data(xorn_revision_t rev, xorn_object_t ob,
			  const struct xornsch_path *data,
			  xorn_error_t *err);

const struct xornsch_picture *xornsch_get_picture_data(xorn_revision_t rev,
						       xorn_object_t ob);
xorn_object_t xornsch_add_picture(xorn_revision_t rev,
				  const struct xornsch_picture *data,
				  xorn_error_t *err);
int xornsch_set_picture_data(xorn_revision_t rev, xorn_object_t ob,
			     const struct xornsch_picture *data,
			     xorn_error_t *err);

const struct xornsch_text *xornsch_get_text_data(xorn_revision_t rev,
						 xorn_object_t ob);
xorn_object_t xornsch_add_text(xorn_revision_t rev,
			       const struct xornsch_text *data,
			       xorn_error_t *err);
int xornsch_set_text_data(xorn_revision_t rev, xorn_object_t ob,
			  const struct xornsch_text *data,
			  xorn_error_t *err);
